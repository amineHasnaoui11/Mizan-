"""Étape 1 du pipeline — preprocessing de l'image (OpenCV).

Objectif (plan §4.1) : rendre la photo exploitable par l'OCR quand elle est
prise au téléphone (angle, ombre, lumière inégale). Enchaînement :
  deskew (perspective) -> binarisation adaptative -> débruitage -> CLAHE.

Optionnel : Google Cloud Vision gère déjà très bien l'angle et la lumière, donc
le preprocessing est surtout utile pour les OCR open-source (PaddleOCR). Piloté
par MIZAN_PREPROCESS (défaut : désactivé).

Dépendances : opencv-python-headless, numpy. Import paresseux pour ne pas
imposer OpenCV au mode Anthropic/LLaVA.
"""
from __future__ import annotations


def _cv():
    import cv2  # import paresseux
    import numpy as np

    return cv2, np


def _deskew(img):
    """Redresse la feuille : détecte le plus grand quadrilatère et l'aplatit."""
    cv2, np = _cv()
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    flou = cv2.GaussianBlur(gris, (5, 5), 0)
    bords = cv2.Canny(flou, 50, 150)
    contours, _ = cv2.findContours(bords, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img
    plus_grand = max(contours, key=cv2.contourArea)
    peri = cv2.arcLength(plus_grand, True)
    approx = cv2.approxPolyDP(plus_grand, 0.02 * peri, True)
    aire = cv2.contourArea(plus_grand)
    # On ne redresse que si on a bien 4 coins couvrant une grande part de l'image.
    if len(approx) != 4 or aire < 0.3 * img.shape[0] * img.shape[1]:
        return img
    pts = approx.reshape(4, 2).astype("float32")
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)
    tl, br = pts[np.argmin(s)], pts[np.argmax(s)]
    tr, bl = pts[np.argmin(diff)], pts[np.argmax(diff)]
    ordered = np.array([tl, tr, br, bl], dtype="float32")
    largeur = int(max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl)))
    hauteur = int(max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl)))
    if largeur < 10 or hauteur < 10:
        return img
    dst = np.array(
        [[0, 0], [largeur - 1, 0], [largeur - 1, hauteur - 1], [0, hauteur - 1]],
        dtype="float32",
    )
    M = cv2.getPerspectiveTransform(ordered, dst)
    return cv2.warpPerspective(img, M, (largeur, hauteur))


def preprocess(image_bytes: bytes, binariser: bool = True) -> bytes:
    """Applique le nettoyage et renvoie l'image encodée en PNG.

    binariser=False garde l'image en niveaux de gris nettoyés (sans seuillage),
    utile si l'OCR préfère du gris au noir/blanc pur.
    """
    cv2, np = _cv()
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return image_bytes  # image illisible : on renvoie l'original

    img = _deskew(img)
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Débruitage (préserve les traits de l'écriture).
    gris = cv2.fastNlMeansDenoising(gris, h=10)
    # CLAHE : fait ressortir l'encre malgré une lumière inégale.
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gris = clahe.apply(gris)
    if binariser:
        gris = cv2.adaptiveThreshold(
            gris, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 15
        )
    ok, buf = cv2.imencode(".png", gris)
    return buf.tobytes() if ok else image_bytes
