"""Configuration centrale, lue depuis l'environnement (.env).

Mizan supporte deux fournisseurs de modèles, choisis via MIZAN_PROVIDER :
  * "anthropic" (défaut) — Claude vision-first, un seul modèle lit + note.
  * "esprit" — Token Factory Esprit (endpoint OpenAI-compatible) : LLaVA
    transcrit la photo, Llama 3.1 70B note. Réseau/VPN Esprit requis.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Fournisseur actif : "anthropic" | "esprit"
PROVIDER = os.getenv("MIZAN_PROVIDER", "anthropic").lower()

# URL du backend, utilisée par l'UI Streamlit.
API_URL = os.getenv("MIZAN_API_URL", "http://localhost:8000")

# max_tokens généreux : une copie multi-questions avec transcription +
# raisonnement par critère peut être longue.
MAX_TOKENS = int(os.getenv("MIZAN_MAX_TOKENS", "8000"))

# --------------------------------------------------------------------------- #
# Fournisseur Anthropic (Claude)
# --------------------------------------------------------------------------- #

# claude-opus-4-8 lit l'arabe ET le français manuscrits et raisonne critère par
# critère — le cœur de valeur du produit.
MODEL = os.getenv("MIZAN_MODEL", "claude-opus-4-8")

# Effort de raisonnement : plus il est haut, plus la notation est rigoureuse
# (au prix de la latence). high est un bon compromis pour la démo.
EFFORT = os.getenv("MIZAN_EFFORT", "high")

# --------------------------------------------------------------------------- #
# Fournisseur Esprit (Token Factory, OpenAI-compatible)
# --------------------------------------------------------------------------- #

ESPRIT_BASE_URL = os.getenv("MIZAN_ESPRIT_BASE_URL", "https://tokenfactory.esprit.tn/api")
# Modèle vision (lit la photo -> texte). LLaVA est faible sur l'arabe manuscrit.
ESPRIT_VISION_MODEL = os.getenv("MIZAN_ESPRIT_VISION_MODEL", "hosted_vllm/llava-1.5-7b-hf")
# Modèle texte (raisonnement / notation).
ESPRIT_TEXT_MODEL = os.getenv(
    "MIZAN_ESPRIT_TEXT_MODEL", "hosted_vllm/Llama-3.1-70B-Instruct"
)
# Le certificat TLS de la Token Factory est interne ; on désactive la
# vérification (comme dans l'exemple fourni par Esprit). "false" pour désactiver.
ESPRIT_VERIFY_TLS = os.getenv("MIZAN_ESPRIT_VERIFY_TLS", "false").lower() in ("1", "true", "yes")

# Moteur de lecture de la copie côté Esprit :
#   "llava"  — VLM vision (défaut historique, faible sur arabe manuscrit)
#   "google" — Google Cloud Vision OCR (recommandé pour le manuscrit)
#   "paddle" — PaddleOCR open-source/offline
OCR = os.getenv("MIZAN_OCR", "llava").lower()

# Preprocessing OpenCV (étape 1) avant l'OCR. Inutile avec Google Vision,
# recommandé avec PaddleOCR. Défaut : désactivé.
PREPROCESS = os.getenv("MIZAN_PREPROCESS", "false").lower() in ("1", "true", "yes")

# Langues EasyOCR. ⚠️ EasyOCR n'autorise l'arabe qu'avec ar/fa/ur/ug/en (pas
# "fr"). "en" lit le script latin, donc le français passe quand même.
EASYOCR_LANGS = [
    s.strip() for s in os.getenv("MIZAN_EASYOCR_LANGS", "ar,en").split(",") if s.strip()
]


def require_api_key() -> str:
    """Retourne la clé API du fournisseur actif, ou lève une erreur explicite."""
    if PROVIDER == "esprit":
        key = os.getenv("ESPRIT_API_KEY")
        if not key:
            raise RuntimeError(
                "ESPRIT_API_KEY manquante. Renseigne ta clé Token Factory dans .env "
                "(et connecte-toi au réseau/VPN Esprit)."
            )
        return key
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY manquante. Copie .env.example vers .env "
            "et renseigne ta clé, ou exporte la variable d'environnement."
        )
    return key
