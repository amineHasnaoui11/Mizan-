"""Cœur métier : appels au VLM Claude pour lire et noter les copies.

Deux modes :
  * corriger_copie()       — 1 appel : image -> transcription + notation + feedback
                             (le plus rapide, bout-en-bout).
  * transcrire_copie() +   — split 2 appels : on transcrit, le prof relit/corrige,
    noter_transcription()    puis on note. C'est le vrai moment human-in-the-loop.

La sortie est garantie conforme au schéma via les *structured outputs*
(`output_config.format`) : Claude ne peut renvoyer qu'un JSON valide.
"""
from __future__ import annotations

import base64
import json

import anthropic

from . import config, prompts
from .schemas import Correction, Reference, build_output_json_schema, build_reference_json_schema

_OUTPUT_SCHEMA = build_output_json_schema()
_REFERENCE_SCHEMA = build_reference_json_schema()


def _client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=config.require_api_key())


def _image_block(image_bytes: bytes, media_type: str) -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
        },
    }


def _image_blocks(images: list[tuple[bytes, str]]) -> list[dict]:
    """Un bloc image par page de la copie."""
    return [_image_block(img, mt) for img, mt in images]


def _texte_reponse(response) -> str:
    """Concatène les blocs texte d'une réponse (ignore les blocs thinking)."""
    return "".join(b.text for b in response.content if b.type == "text")


# --------------------------------------------------------------------------- #
# Construction du barème à partir des documents du prof (Claude vision)
# --------------------------------------------------------------------------- #


def construire_reference(
    devoir_images: list[tuple[bytes, str]],
    bareme_images: list[tuple[bytes, str]],
    corrige_images: list[tuple[bytes, str]],
    matiere: str = "",
    niveau: str = "",
    langue: str = "mixte",
    devoir_id: str = "",
) -> dict:
    """Construit le barème structuré à partir des documents scannés du prof.

    Claude lit directement les images (devoir vierge, barème, corrigé) et
    produit une référence conforme au schéma, via structured outputs.
    """
    contenu: list[dict] = []

    def _ajouter(titre: str, images: list[tuple[bytes, str]]) -> None:
        if not images:
            return
        contenu.append({"type": "text", "text": f"=== {titre} ==="})
        contenu.extend(_image_blocks(images))

    _ajouter("DEVOIR (énoncés)", devoir_images)
    _ajouter("BARÈME (points)", bareme_images)
    _ajouter("CORRIGÉ DU PROF (réponses attendues)", corrige_images)
    if not contenu:
        raise ValueError("Aucun document fourni.")

    consigne = prompts.USER_CONSTRUCTION.format(
        matiere=matiere,
        niveau=niveau,
        langue=langue,
        devoir_id=devoir_id or "devoir",
        texte_devoir="[voir images DEVOIR]",
        texte_bareme="[voir images BARÈME]",
        texte_corrige="[voir images CORRIGÉ]",
        schema="(fourni par le format de sortie)",
    )
    contenu.append({"type": "text", "text": consigne})

    response = _client().messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=prompts.SYSTEM_CONSTRUCTION,
        output_config={
            "effort": config.EFFORT,
            "format": {"type": "json_schema", "schema": _REFERENCE_SCHEMA},
        },
        messages=[{"role": "user", "content": contenu}],
    )
    data = json.loads(_texte_reponse(response))
    if matiere:
        data.setdefault("matiere", matiere)
    if niveau:
        data.setdefault("niveau", niveau)
    if devoir_id:
        data["devoir_id"] = devoir_id
    return Reference.model_validate(data).model_dump()


# --------------------------------------------------------------------------- #
# Mode 1 appel : image -> correction complète
# --------------------------------------------------------------------------- #


def corriger_copie(
    reference: dict,
    images: list[tuple[bytes, str]],
    copie_id: str,
    avec_corrige: bool = True,
) -> Correction:
    """Corrige une copie (1 ou plusieurs pages) en un seul appel.

    `images` : liste de (image_bytes, media_type), une entrée par page.
    avec_corrige=False bascule en Option 3 (raisonnement libre, sans corrigé).
    """
    ref_json = prompts.reference_pour_prompt(reference, avec_corrige=avec_corrige)
    gabarit = (
        prompts.USER_CORRECTION if avec_corrige else prompts.USER_CORRECTION_SANS_CORRIGE
    )
    user_text = gabarit.format(reference_json=ref_json, copie_id=copie_id)

    response = _client().messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=prompts.SYSTEM_CORRECTION,
        output_config={
            "effort": config.EFFORT,
            "format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA},
        },
        messages=[
            {
                "role": "user",
                "content": [
                    *_image_blocks(images),
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )
    data = json.loads(_texte_reponse(response))
    return Correction.model_validate(data)


# --------------------------------------------------------------------------- #
# Mode 2 appels : étape 1 — transcription seule
# --------------------------------------------------------------------------- #


def transcrire_copie(
    reference: dict,
    images: list[tuple[bytes, str]],
    copie_id: str,
) -> dict:
    """Lit la copie (1 ou plusieurs pages) et renvoie les transcriptions.

    `images` : liste de (image_bytes, media_type), une entrée par page.
    Renvoie {"copie_id", "langue_detectee", "transcriptions": [{numero, transcription}]}.
    """
    questions = [
        {"numero": q["numero"], "enonce": q.get("enonce", "")}
        for q in reference.get("questions", [])
    ]
    user_text = prompts.USER_TRANSCRIPTION.format(
        questions_json=json.dumps(questions, ensure_ascii=False, indent=2),
        copie_id=copie_id,
    )
    schema = {
        "type": "object",
        "properties": {
            "copie_id": {"type": "string"},
            "langue_detectee": {"type": "string", "enum": ["fr", "ar", "mixte"]},
            "transcriptions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "numero": {"type": "integer"},
                        "transcription": {"type": "string"},
                    },
                    "required": ["numero", "transcription"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["copie_id", "langue_detectee", "transcriptions"],
        "additionalProperties": False,
    }
    response = _client().messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=prompts.SYSTEM_TRANSCRIPTION,
        output_config={
            "effort": config.EFFORT,
            "format": {"type": "json_schema", "schema": schema},
        },
        messages=[
            {
                "role": "user",
                "content": [
                    *_image_blocks(images),
                    {"type": "text", "text": user_text},
                ],
            }
        ],
    )
    return json.loads(_texte_reponse(response))


# --------------------------------------------------------------------------- #
# Mode 2 appels : étape 2 — notation d'une transcription (validée par le prof)
# --------------------------------------------------------------------------- #


def noter_transcription(
    reference: dict,
    transcriptions: list[dict],
    copie_id: str,
) -> Correction:
    """Note une transcription (déjà relue/corrigée par le prof), sans image.

    transcriptions : [{"numero": <int>, "transcription": <str>}, ...]
    """
    ref_json = prompts.reference_pour_prompt(reference, avec_corrige=True)
    user_text = prompts.USER_NOTATION.format(
        reference_json=ref_json,
        copie_id=copie_id,
        transcriptions_json=json.dumps(transcriptions, ensure_ascii=False, indent=2),
    )
    response = _client().messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_TOKENS,
        system=prompts.SYSTEM_NOTATION,
        output_config={
            "effort": config.EFFORT,
            "format": {"type": "json_schema", "schema": _OUTPUT_SCHEMA},
        },
        messages=[{"role": "user", "content": user_text}],
    )
    data = json.loads(_texte_reponse(response))
    return Correction.model_validate(data)
