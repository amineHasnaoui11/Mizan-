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

app = FastAPI(title="Mizan API", version=__version__)

_MEDIA_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}


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


async def _read_image(copie: UploadFile) -> tuple[bytes, str]:
    media_type = copie.content_type or "image/jpeg"
    if media_type not in _MEDIA_TYPES:
        raise HTTPException(
            415,
            f"Type d'image non supporté : {media_type}. "
            f"Attendus : {', '.join(sorted(_MEDIA_TYPES))}.",
        )
    data = await copie.read()
    if not data:
        raise HTTPException(400, "Fichier image vide.")
    return data, media_type


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
        "endpoints": ["/corriger", "/transcrire", "/noter"],
    }


@app.post("/corriger")
async def corriger(
    reference: str = Form(...),
    copie_id: str = Form(...),
    copie: UploadFile = File(...),
    avec_corrige: bool = Form(True),
) -> dict:
    """1 appel : image + référence -> correction complète."""
    ref = _parse_reference(reference)
    image_bytes, media_type = await _read_image(copie)
    resultat = _handle_anthropic_errors(
        lambda: correcteur.corriger_copie(
            ref, image_bytes, media_type, copie_id, avec_corrige=avec_corrige
        )
    )
    return resultat.model_dump()


@app.post("/transcrire")
async def transcrire(
    reference: str = Form(...),
    copie_id: str = Form(...),
    copie: UploadFile = File(...),
) -> dict:
    """Split étape 1 : image -> transcriptions par question (à relire par le prof)."""
    ref = _parse_reference(reference)
    image_bytes, media_type = await _read_image(copie)
    return _handle_anthropic_errors(
        lambda: correcteur.transcrire_copie(ref, image_bytes, media_type, copie_id)
    )


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
