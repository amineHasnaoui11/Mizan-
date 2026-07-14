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

# --------------------------------------------------------------------------- #
# Fournisseur Groq (public, gratuit, OpenAI-compatible) — Llama 3.3 70B.
# Marche sur internet public (contrairement à Esprit qui exige le réseau interne),
# donc indispensable dès qu'on héberge ou qu'on teste hors réseau Esprit.
# --------------------------------------------------------------------------- #

GROQ_BASE_URL = os.getenv("MIZAN_GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_TEXT_MODEL = os.getenv("MIZAN_GROQ_TEXT_MODEL", "llama-3.3-70b-versatile")
GROQ_VISION_MODEL = os.getenv(
    "MIZAN_GROQ_VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"
)

# --------------------------------------------------------------------------- #
# Résolution du LLM OpenAI-compatible actif (esprit OU groq).
# llm_esprit lit ces valeurs génériques.
# --------------------------------------------------------------------------- #

if PROVIDER == "groq":
    LLM_BASE_URL = GROQ_BASE_URL
    LLM_TEXT_MODEL = GROQ_TEXT_MODEL
    LLM_VISION_MODEL = GROQ_VISION_MODEL
    LLM_VERIFY_TLS = True
else:  # esprit (défaut OpenAI-compatible)
    LLM_BASE_URL = ESPRIT_BASE_URL
    LLM_TEXT_MODEL = ESPRIT_TEXT_MODEL
    LLM_VISION_MODEL = ESPRIT_VISION_MODEL
    LLM_VERIFY_TLS = ESPRIT_VERIFY_TLS

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

# Google Cloud Vision : deux modes d'authentification.
#   * Clé API simple (GOOGLE_API_KEY) — une chaîne, aucun fichier. Utile quand
#     l'organisation bloque les clés JSON de compte de service
#     (iam.disableServiceAccountKeyCreation).
#   * Sinon, le client retombe sur GOOGLE_APPLICATION_CREDENTIALS (clé JSON).
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "").strip()


def require_api_key() -> str:
    """Retourne la clé API du fournisseur actif, ou lève une erreur explicite."""
    if PROVIDER == "groq":
        key = os.getenv("GROQ_API_KEY")
        if not key:
            raise RuntimeError(
                "GROQ_API_KEY manquante. Crée une clé gratuite sur console.groq.com "
                "et renseigne-la dans .env."
            )
        return key
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
