"""Étapes 2-3 du pipeline — OCR + structuration.

Extrait le texte manuscrit de la copie et le renvoie tel quel (texte brut).
La « structuration » fine par question est déléguée au LLM de notation, qui
sait rattacher chaque réponse à sa question à partir de la référence — plus
robuste que des heuristiques de découpage sur de l'arabe manuscrit.

Moteurs disponibles (config.MIZAN_OCR) :
  * "google" — Google Cloud Vision (document_text_detection). RECOMMANDÉ pour
    le manuscrit (plan §4.2). Nécessite GOOGLE_APPLICATION_CREDENTIALS.
  * "paddle" — PaddleOCR, open-source/offline (plus faible sur manuscrit dur).

Le moteur "llava" (VLM vision) est géré directement dans llm_esprit, pas ici.
Imports paresseux : on n'impose google/paddle qu'au moment où on les utilise.
"""
from __future__ import annotations

from . import config, preprocessing


def _maybe_preprocess(image_bytes: bytes, binariser: bool) -> bytes:
    if config.PREPROCESS:
        return preprocessing.preprocess(image_bytes, binariser=binariser)
    return image_bytes


# --------------------------------------------------------------------------- #
# Google Cloud Vision
# --------------------------------------------------------------------------- #


def ocr_google(image_bytes: bytes) -> str:
    """Texte extrait par Google Cloud Vision (manuscrit + imprimé, ar/fr)."""
    from google.cloud import vision  # import paresseux

    # Vision gère déjà l'angle/lumière : binarisation désactivée par défaut ici.
    data = _maybe_preprocess(image_bytes, binariser=False)
    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=data)
    resp = client.document_text_detection(
        image=image,
        image_context={"language_hints": ["ar", "fr"]},
    )
    if resp.error.message:
        raise RuntimeError(f"Google Vision : {resp.error.message}")
    return (resp.full_text_annotation.text or "").strip()


# --------------------------------------------------------------------------- #
# PaddleOCR (open-source / offline)
# --------------------------------------------------------------------------- #

_paddle = None


def ocr_paddle(image_bytes: bytes) -> str:
    """Texte extrait par PaddleOCR (arabe). Modèle chargé une seule fois."""
    global _paddle
    import numpy as np
    from paddleocr import PaddleOCR  # import paresseux

    if _paddle is None:
        _paddle = PaddleOCR(use_angle_cls=True, lang="ar", show_log=False)

    data = _maybe_preprocess(image_bytes, binariser=True)
    import cv2

    arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    result = _paddle.ocr(arr, cls=True)
    lignes: list[str] = []
    for page in result or []:
        for ligne in page or []:
            # ligne = [box, (texte, score)]
            try:
                lignes.append(ligne[1][0])
            except (IndexError, TypeError):
                continue
    return "\n".join(lignes).strip()


# --------------------------------------------------------------------------- #
# Dispatcher
# --------------------------------------------------------------------------- #


def extraire_texte(image_bytes: bytes) -> str:
    """Renvoie le texte OCR de la copie selon config.MIZAN_OCR."""
    moteur = config.OCR
    if moteur == "google":
        return ocr_google(image_bytes)
    if moteur == "paddle":
        return ocr_paddle(image_bytes)
    raise ValueError(
        f"Moteur OCR inconnu : {moteur!r} (attendus : google, paddle, llava)"
    )
