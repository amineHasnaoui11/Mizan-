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
from .schemas import Correction, Reference, build_output_json_schema, build_reference_json_schema

_OUTPUT_SCHEMA = build_output_json_schema()
_REFERENCE_SCHEMA = build_reference_json_schema()


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
# Construction du barème à partir des documents du prof
# (barème + devoir vierge + corrigé) -> référence structurée
# --------------------------------------------------------------------------- #


def _ocr_groupe(images: list[tuple[bytes, str]]) -> str:
    """OCR d'un ensemble de pages (un document), concaténées par page."""
    from . import ocr

    if not images:
        return ""
    morceaux = []
    for idx, (img, _mt) in enumerate(images, 1):
        texte = ocr.extraire_texte(img)
        morceaux.append(f"--- page {idx} ---\n{texte}" if len(images) > 1 else texte)
    return "\n\n".join(morceaux).strip()


def assistant_libre(
    images: list[tuple[bytes, str]],
    consigne: str = "",
) -> str:
    """Mode assistant : lit une feuille (exercice) et renvoie un corrigé libre.

    Aucun barème/devoir requis — comme un chat avec l'IA, mais avec le scan.
    """
    consigne = consigne.strip() or "Donne le corrigé détaillé de cet exercice."

    if config.OCR in ("google", "easyocr", "paddle"):
        contenu = _ocr_groupe(images)
        if not contenu:
            raise ValueError("Aucun texte lisible dans la feuille.")
        resp = _client().chat.completions.create(
            model=config.ESPRIT_TEXT_MODEL,
            max_tokens=config.MAX_TOKENS,
            temperature=0.2,
            messages=[
                {"role": "system", "content": prompts.SYSTEM_ASSISTANT},
                {"role": "user", "content": prompts.USER_ASSISTANT.format(consigne=consigne, contenu=contenu)},
            ],
        )
        return (resp.choices[0].message.content or "").strip()

    # Mode LLaVA (vision) — toutes les pages en un appel.
    contenu_msg = [{"type": "text", "text": f"{prompts.SYSTEM_ASSISTANT}\n\n{consigne}"}]
    for img, mt in images:
        contenu_msg.append({"type": "image_url", "image_url": {"url": _data_uri(img, mt)}})
    resp = _client().chat.completions.create(
        model=config.ESPRIT_VISION_MODEL,
        max_tokens=1500,
        temperature=0.2,
        messages=[{"role": "user", "content": contenu_msg}],
    )
    return (resp.choices[0].message.content or "").strip()


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

    Lit (OCR) le devoir vierge, le barème et le corrigé, puis demande à Llama
    de fusionner le tout en une référence conforme au schéma. Le prof relit et
    corrige ensuite (human-in-the-loop).
    """
    if config.OCR not in ("google", "easyocr", "paddle"):
        raise RuntimeError(
            "La construction du barème nécessite un moteur OCR "
            "(MIZAN_OCR=google|easyocr|paddle), pas LLaVA."
        )
    texte_devoir = _ocr_groupe(devoir_images)
    texte_bareme = _ocr_groupe(bareme_images)
    texte_corrige = _ocr_groupe(corrige_images)
    if not (texte_devoir or texte_bareme or texte_corrige):
        raise ValueError("Aucun texte lisible dans les documents fournis.")

    user_text = prompts.USER_CONSTRUCTION.format(
        matiere=matiere,
        niveau=niveau,
        langue=langue,
        devoir_id=devoir_id or "devoir",
        texte_devoir=texte_devoir or "(non fourni)",
        texte_bareme=texte_bareme or "(non fourni)",
        texte_corrige=texte_corrige or "(non fourni)",
        schema=json.dumps(_REFERENCE_SCHEMA, ensure_ascii=False),
    )
    resp = _client().chat.completions.create(
        model=config.ESPRIT_TEXT_MODEL,
        max_tokens=config.MAX_TOKENS,
        temperature=0.1,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompts.SYSTEM_CONSTRUCTION},
            {"role": "user", "content": user_text},
        ],
    )
    data = _extract_json(resp.choices[0].message.content or "")
    if matiere:
        data.setdefault("matiere", matiere)
    if niveau:
        data.setdefault("niveau", niveau)
    if devoir_id:
        data["devoir_id"] = devoir_id
    # Valide/normalise (lève si non conforme) puis renvoie un dict propre.
    return Reference.model_validate(data).model_dump()


# --------------------------------------------------------------------------- #
# Étape 3 — structuration : répartir un texte OCR brut par question (Llama texte)
# --------------------------------------------------------------------------- #


def structurer_texte(reference: dict, texte_ocr: str) -> dict:
    """Découpe un bloc OCR brut en transcriptions par question (via Llama).

    Renvoie {"langue_detectee": ..., "transcriptions": [{numero, transcription}]}.
    En cas d'échec du modèle, on retombe sur tout le texte sous la 1re question.
    """
    questions = reference.get("questions", [])
    numeros = [q.get("numero") for q in questions]
    questions_min = [
        {"numero": q.get("numero"), "enonce": q.get("enonce", "")} for q in questions
    ]
    user_text = prompts.USER_STRUCTURATION.format(
        questions_json=json.dumps(questions_min, ensure_ascii=False, indent=2),
        texte_ocr=texte_ocr,
    )
    try:
        resp = _client().chat.completions.create(
            model=config.ESPRIT_TEXT_MODEL,
            max_tokens=config.MAX_TOKENS,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompts.SYSTEM_STRUCTURATION},
                {"role": "user", "content": user_text},
            ],
        )
        data = _extract_json(resp.choices[0].message.content or "")
        transcriptions = data.get("transcriptions") or []
        # Ne garde que les numéros connus ; complète les questions manquantes.
        par_numero = {
            t.get("numero"): (t.get("transcription") or "")
            for t in transcriptions
            if t.get("numero") in numeros
        }
        transcriptions = [
            {"numero": n, "transcription": par_numero.get(n, "")} for n in numeros
        ]
        if not any(t["transcription"].strip() for t in transcriptions):
            raise ValueError("structuration vide")
        return {
            "langue_detectee": data.get("langue_detectee", "mixte"),
            "transcriptions": transcriptions,
        }
    except Exception:
        premier = numeros[0] if numeros else 1
        return {
            "langue_detectee": "mixte",
            "transcriptions": [{"numero": premier, "transcription": texte_ocr}],
        }


# --------------------------------------------------------------------------- #
# Étape 1-3 — transcription : OCR (Google/Paddle) OU LLaVA (vision)
# --------------------------------------------------------------------------- #


def transcrire_copie(
    reference: dict,
    images: list[tuple[bytes, str]],
    copie_id: str,
) -> dict:
    """Lit une copie (1 ou plusieurs pages) et renvoie
    {copie_id, langue_detectee, transcriptions}.

    `images` : liste de (image_bytes, media_type), une entrée par page.

    Aiguillage selon MIZAN_OCR :
      * "google"/"easyocr"/"paddle" — OCR page par page, textes concaténés,
        puis structuration par question (Llama, étape 3 du plan) avant prof.
      * "llava" — VLM vision (fallback historique), toutes les pages en 1 appel.
    """
    from . import ocr

    questions = reference.get("questions", [])
    numeros = [q.get("numero") for q in questions]

    if config.OCR in ("google", "easyocr", "paddle"):
        morceaux = []
        for idx, (img, _mt) in enumerate(images, 1):
            texte_page = ocr.extraire_texte(img)
            if len(images) > 1:
                morceaux.append(f"=== الصفحة {idx} ===\n{texte_page}")
            else:
                morceaux.append(texte_page)
        texte = "\n\n".join(morceaux)
        structure = structurer_texte(reference, texte)
        return {
            "copie_id": copie_id,
            "langue_detectee": structure["langue_detectee"],
            "transcriptions": structure["transcriptions"],
        }

    # --- Mode LLaVA (vision) — toutes les pages dans un seul appel ---
    liste = "\n".join(
        f"- Q{q.get('numero')}: {q.get('enonce', '')}" for q in questions
    )
    prompt = (
        "Lis attentivement cette copie manuscrite d'élève (français et/ou arabe), "
        "sur une ou plusieurs pages. "
        "Transcris fidèlement ce que l'élève a écrit, sans corriger ses fautes. "
        "Si un passage est illisible, écris [illisible].\n\n"
        f"Questions attendues :\n{liste}\n\n"
        "Réponds UNIQUEMENT en JSON, sans autre texte, au format :\n"
        '{"langue_detectee": "fr|ar|mixte", "transcriptions": '
        '[{"numero": <int>, "transcription": "<texte lu>"}]}'
    )

    contenu_msg = [{"type": "text", "text": prompt}]
    for img, mt in images:
        contenu_msg.append(
            {"type": "image_url", "image_url": {"url": _data_uri(img, mt)}}
        )
    resp = _client().chat.completions.create(
        model=config.ESPRIT_VISION_MODEL,
        max_tokens=1500,
        temperature=0.1,
        messages=[{"role": "user", "content": contenu_msg}],
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
    images: list[tuple[bytes, str]],
    copie_id: str,
    avec_corrige: bool = True,
) -> Correction:
    """Correction complète côté Esprit : OCR/LLaVA transcrit puis Llama note.

    `images` : liste de (image_bytes, media_type), une entrée par page.
    avec_corrige est ignoré ici (l'Option 3 sans corrigé reste Anthropic-only).
    """
    trans = transcrire_copie(reference, images, copie_id)
    return noter_transcription(reference, trans["transcriptions"], copie_id)
