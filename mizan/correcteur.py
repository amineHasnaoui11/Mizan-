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
from .schemas import Correction, build_output_json_schema

_OUTPUT_SCHEMA = build_output_json_schema()


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


def _texte_reponse(response) -> str:
    """Concatène les blocs texte d'une réponse (ignore les blocs thinking)."""
    return "".join(b.text for b in response.content if b.type == "text")


# --------------------------------------------------------------------------- #
# Mode 1 appel : image -> correction complète
# --------------------------------------------------------------------------- #


def corriger_copie(
    reference: dict,
    image_bytes: bytes,
    media_type: str,
    copie_id: str,
    avec_corrige: bool = True,
) -> Correction:
    """Corrige une copie en un seul appel (transcription + notation + feedback).

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
                    _image_block(image_bytes, media_type),
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
    image_bytes: bytes,
    media_type: str,
    copie_id: str,
) -> dict:
    """Lit la copie et renvoie les transcriptions par question, sans noter.

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
                    _image_block(image_bytes, media_type),
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
