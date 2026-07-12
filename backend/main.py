"""API FastAPI de Mizan.

Endpoints :
  GET  /              — santé / infos
  POST /corriger      — 1 appel : image + référence -> correction complète
  POST /transcrire    — split étape 1 : image -> transcriptions par question
  POST /noter         — split étape 2 : transcriptions validées -> correction

La référence est passée en champ de formulaire `reference` (JSON stringifié),
l'image en fichier `copie`. Cela permet un upload multipart simple depuis
Streamlit ou curl.
"""
from __future__ import annotations

import json

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ValidationError

from mizan import __version__, config, correcteur
from mizan.schemas import Reference

from . import store

app = FastAPI(title="Mizan API", version=__version__)

_MEDIA_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
_PDF_TYPES = {"application/pdf", "application/x-pdf"}
# On vise ~2200 px sur le grand côté : assez pour l'OCR manuscrit, sans
# produire des images énormes (limite Google Vision ~20 Mo/image).
_PDF_MAX_COTE = 2200


def _pdf_to_images(data: bytes) -> list[tuple[bytes, str]]:
    """Rend chaque page d'un PDF en JPEG (une image par page), taille bornée."""
    try:
        import fitz  # PyMuPDF, import paresseux
    except ImportError as e:  # pragma: no cover
        raise HTTPException(
            500,
            "Lecture PDF indisponible : installe PyMuPDF (pip install pymupdf).",
        ) from e
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        raise HTTPException(400, f"PDF illisible : {e}") from e
    pages: list[tuple[bytes, str]] = []
    for page in doc:
        cote = max(page.rect.width, page.rect.height) or 1
        zoom = min(2.0, _PDF_MAX_COTE / cote)  # jamais plus de 2x
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        pages.append((pix.tobytes("jpeg"), "image/jpeg"))
    if not pages:
        raise HTTPException(400, "PDF sans page.")
    return pages


def _parse_reference(reference_str: str) -> dict:
    try:
        data = json.loads(reference_str)
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"Référence JSON invalide : {e}") from e
    try:
        Reference.model_validate(data)  # validation de structure
    except ValidationError as e:
        raise HTTPException(422, f"Référence non conforme au schéma : {e}") from e
    return data


async def _read_fichier(copie: UploadFile) -> list[tuple[bytes, str]]:
    """Lit un fichier uploadé -> liste de (bytes, media_type).

    Une image -> une entrée. Un PDF -> une entrée par page.
    """
    media_type = copie.content_type or "image/jpeg"
    nom = (copie.filename or "").lower()
    data = await copie.read()
    if not data:
        raise HTTPException(400, "Fichier vide.")
    if media_type in _PDF_TYPES or nom.endswith(".pdf"):
        return _pdf_to_images(data)
    if media_type not in _MEDIA_TYPES:
        raise HTTPException(
            415,
            f"Type non supporté : {media_type}. "
            f"Attendus : {', '.join(sorted(_MEDIA_TYPES))}, application/pdf.",
        )
    return [(data, media_type)]


async def _read_images(copies: list[UploadFile]) -> list[tuple[bytes, str]]:
    """Lit toutes les pages d'une copie (images et/ou PDF multi-pages)."""
    if not copies:
        raise HTTPException(400, "Aucun fichier fourni.")
    images: list[tuple[bytes, str]] = []
    for c in copies:
        images.extend(await _read_fichier(c))
    return images


def _handle_anthropic_errors(fn):
    """Convertit les erreurs API en réponses HTTP lisibles."""
    try:
        return fn()
    except RuntimeError as e:  # clé API manquante
        raise HTTPException(500, str(e)) from e
    except Exception as e:  # erreurs SDK Anthropic, parsing, etc.
        raise HTTPException(502, f"Erreur du modèle : {e}") from e


@app.get("/")
def racine() -> dict:
    return {
        "service": "Mizan",
        "version": __version__,
        "modele": config.MODEL,
        "effort": config.EFFORT,
        "endpoints": ["/construire-reference", "/corriger", "/transcrire", "/noter"],
    }


@app.post("/corriger")
async def corriger(
    reference: str = Form(...),
    copie_id: str = Form(...),
    copie: list[UploadFile] = File(...),
    avec_corrige: bool = Form(True),
) -> dict:
    """1 appel : image(s) + référence -> correction complète.

    `copie` accepte plusieurs fichiers = les pages d'une même copie.
    """
    ref = _parse_reference(reference)
    images = await _read_images(copie)
    resultat = _handle_anthropic_errors(
        lambda: correcteur.corriger_copie(
            ref, images, copie_id, avec_corrige=avec_corrige
        )
    )
    return resultat.model_dump()


@app.post("/transcrire")
async def transcrire(
    reference: str = Form(...),
    copie_id: str = Form(...),
    copie: list[UploadFile] = File(...),
) -> dict:
    """Split étape 1 : image(s) -> transcriptions par question (à relire).

    `copie` accepte plusieurs fichiers = les pages d'une même copie.
    """
    ref = _parse_reference(reference)
    images = await _read_images(copie)
    return _handle_anthropic_errors(
        lambda: correcteur.transcrire_copie(ref, images, copie_id)
    )


@app.post("/construire-reference")
async def construire_reference(
    devoir: list[UploadFile] = File(default=[]),
    bareme: list[UploadFile] = File(default=[]),
    corrige: list[UploadFile] = File(default=[]),
    matiere: str = Form(""),
    niveau: str = Form(""),
    langue: str = Form("mixte"),
    devoir_id: str = Form(""),
) -> dict:
    """Construit le barème structuré à partir des documents du prof.

    `devoir` (énoncés vierges), `bareme` (points), `corrige` (réponses attendues)
    acceptent chacun plusieurs fichiers (images ou PDF). Retourne une référence
    éditable par le prof avant de noter les copies.
    """
    devoir_imgs = await _read_images(devoir) if devoir else []
    bareme_imgs = await _read_images(bareme) if bareme else []
    corrige_imgs = await _read_images(corrige) if corrige else []
    if not (devoir_imgs or bareme_imgs or corrige_imgs):
        raise HTTPException(400, "Fournis au moins un document (devoir, barème ou corrigé).")
    return _handle_anthropic_errors(
        lambda: correcteur.construire_reference(
            devoir_imgs, bareme_imgs, corrige_imgs,
            matiere=matiere, niveau=niveau, langue=langue, devoir_id=devoir_id,
        )
    )


@app.get("/devoirs")
def lister_devoirs() -> list[dict]:
    """Résumé des devoirs enregistrés (partagé web + mobile)."""
    return store.lister()


@app.get("/devoirs/{devoir_id}")
def obtenir_devoir(devoir_id: str) -> dict:
    ref = store.charger(devoir_id)
    if ref is None:
        raise HTTPException(404, "Devoir introuvable.")
    return ref


@app.post("/devoirs")
def enregistrer_devoir(reference: dict) -> dict:
    """Enregistre (ou met à jour) un devoir. Le corps est une référence."""
    try:
        Reference.model_validate(reference)
    except ValidationError as e:
        raise HTTPException(422, f"Référence non conforme : {e}") from e
    devoir_id = store.enregistrer(reference)
    return {"devoir_id": devoir_id, "ok": True}


@app.delete("/devoirs/{devoir_id}")
def supprimer_devoir(devoir_id: str) -> dict:
    return {"supprime": store.supprimer(devoir_id)}


class NoterPayload(BaseModel):
    reference: dict
    copie_id: str
    transcriptions: list[dict]


@app.post("/noter")
async def noter(payload: NoterPayload) -> dict:
    """Split étape 2 : transcriptions (validées par le prof) -> correction notée."""
    try:
        Reference.model_validate(payload.reference)
    except ValidationError as e:
        raise HTTPException(422, f"Référence non conforme : {e}") from e
    resultat = _handle_anthropic_errors(
        lambda: correcteur.noter_transcription(
            payload.reference, payload.transcriptions, payload.copie_id
        )
    )
    return resultat.model_dump()
