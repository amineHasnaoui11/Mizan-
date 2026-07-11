"""Fournisseur Esprit (Token Factory) — endpoint OpenAI-compatible.

Pipeline en deux modèles, chacun sur son point fort :
  * LLaVA (vision)   lit la photo et transcrit le texte de l'élève.
  * Llama 3.1 70B    note critère par critère (bien plus fort en raisonnement).

Le split colle exactement au human-in-the-loop : LLaVA transcrit, le prof relit
et corrige, Llama note la version validée.

⚠️ LLaVA 1.5 7B est un petit modèle ancien : faible sur l'arabe manuscrit.
Attends-toi à des transcriptions imparfaites — d'où l'intérêt de l'édition prof.
Nécessite le réseau/VPN Esprit (endpoint interne).
"""
from __future__ import annotations

import base64
import json
import warnings

import httpx
from openai import OpenAI

from . import config, prompts
from .schemas import Correction, build_output_json_schema

_OUTPUT_SCHEMA = build_output_json_schema()


def _client() -> OpenAI:
    api_key = config.require_api_key()
    if not config.ESPRIT_VERIFY_TLS:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    http_client = httpx.Client(verify=config.ESPRIT_VERIFY_TLS, timeout=180.0)
    return OpenAI(
        api_key=api_key,
        base_url=config.ESPRIT_BASE_URL,
        http_client=http_client,
    )


def _data_uri(image_bytes: bytes, media_type: str) -> str:
    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    return f"data:{media_type};base64,{b64}"


def _extract_json(text: str) -> dict:
    """Parse un JSON même si le modèle l'entoure de texte (fréquent avec LLaVA)."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Retire d'éventuelles clôtures markdown ```json ... ```
    if "```" in text:
        text = text.split("```")[1]
        text = text[4:] if text.lstrip().lower().startswith("json") else text
    i, j = text.find("{"), text.rfind("}")
    if i != -1 and j != -1 and j > i:
        return json.loads(text[i : j + 1])
    raise ValueError("Réponse du modèle sans JSON exploitable")


# --------------------------------------------------------------------------- #
# Étape 1-3 — transcription : OCR (Google/Paddle) OU LLaVA (vision)
# --------------------------------------------------------------------------- #


def transcrire_copie(
    reference: dict,
    image_bytes: bytes,
    media_type: str,
    copie_id: str,
) -> dict:
    """Lit la copie et renvoie {copie_id, langue_detectee, transcriptions}.

    Aiguillage selon MIZAN_OCR :
      * "google"/"easyocr"/"paddle" — OCR : texte complet mis sous la 1re
        question, la structuration fine est laissée au LLM de notation.
      * "llava" — VLM vision (fallback historique).
    """
    from . import ocr

    questions = reference.get("questions", [])
    numeros = [q.get("numero") for q in questions]

    if config.OCR in ("google", "easyocr", "paddle"):
        texte = ocr.extraire_texte(image_bytes)
        premier = numeros[0] if numeros else 1
        return {
            "copie_id": copie_id,
            "langue_detectee": "mixte",
            "transcriptions": [{"numero": premier, "transcription": texte}],
        }

    # --- Mode LLaVA (vision) ---
    liste = "\n".join(
        f"- Q{q.get('numero')}: {q.get('enonce', '')}" for q in questions
    )
    prompt = (
        "Lis attentivement cette copie manuscrite d'élève (français et/ou arabe). "
        "Transcris fidèlement ce que l'élève a écrit, sans corriger ses fautes. "
        "Si un passage est illisible, écris [illisible].\n\n"
        f"Questions attendues :\n{liste}\n\n"
        "Réponds UNIQUEMENT en JSON, sans autre texte, au format :\n"
        '{"langue_detectee": "fr|ar|mixte", "transcriptions": '
        '[{"numero": <int>, "transcription": "<texte lu>"}]}'
    )

    resp = _client().chat.completions.create(
        model=config.ESPRIT_VISION_MODEL,
        max_tokens=1500,
        temperature=0.1,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": _data_uri(image_bytes, media_type)}},
                ],
            }
        ],
    )
    contenu = resp.choices[0].message.content or ""
    try:
        data = _extract_json(contenu)
        transcriptions = data.get("transcriptions") or []
        if not transcriptions:
            raise ValueError("aucune transcription")
        langue = data.get("langue_detectee", "mixte")
    except Exception:
        # Fallback : LLaVA a renvoyé du texte libre -> on le range sous Q1.
        premier = numeros[0] if numeros else 1
        transcriptions = [{"numero": premier, "transcription": contenu.strip()}]
        langue = "mixte"
    return {
        "copie_id": copie_id,
        "langue_detectee": langue,
        "transcriptions": transcriptions,
    }


# --------------------------------------------------------------------------- #
# Étape 2 — notation (Llama 3.1 70B, texte)
# --------------------------------------------------------------------------- #


def noter_transcription(
    reference: dict,
    transcriptions: list[dict],
    copie_id: str,
) -> Correction:
    """Note une transcription (validée par le prof) avec Llama 3.1 70B."""
    ref_json = prompts.reference_pour_prompt(reference, avec_corrige=True)
    schema_txt = json.dumps(_OUTPUT_SCHEMA, ensure_ascii=False)
    user_text = (
        prompts.USER_NOTATION.format(
            reference_json=ref_json,
            copie_id=copie_id,
            transcriptions_json=json.dumps(transcriptions, ensure_ascii=False, indent=2),
        )
        + "\n\nLe JSON doit être STRICTEMENT conforme à ce schéma :\n"
        + schema_txt
    )

    resp = _client().chat.completions.create(
        model=config.ESPRIT_TEXT_MODEL,
        max_tokens=config.MAX_TOKENS,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompts.SYSTEM_NOTATION},
            {"role": "user", "content": user_text},
        ],
    )
    data = _extract_json(resp.choices[0].message.content or "")
    return Correction.model_validate(data)


# --------------------------------------------------------------------------- #
# Mode « 1 clic » — enchaîne LLaVA puis Llama
# --------------------------------------------------------------------------- #


def corriger_copie(
    reference: dict,
    image_bytes: bytes,
    media_type: str,
    copie_id: str,
    avec_corrige: bool = True,
) -> Correction:
    """Correction complète côté Esprit : LLaVA transcrit puis Llama note.

    avec_corrige est ignoré ici (l'Option 3 sans corrigé reste Anthropic-only).
    """
    trans = transcrire_copie(reference, image_bytes, media_type, copie_id)
    return noter_transcription(reference, trans["transcriptions"], copie_id)
