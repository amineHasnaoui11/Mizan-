"""Configuration centrale, lue depuis l'environnement (.env)."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# Modèle vision Claude. claude-opus-4-8 lit l'arabe ET le français manuscrits
# et raisonne critère par critère — le cœur de valeur du produit.
MODEL = os.getenv("MIZAN_MODEL", "claude-opus-4-8")

# Effort de raisonnement : plus il est haut, plus la notation est rigoureuse
# (au prix de la latence). high est un bon compromis pour la démo.
EFFORT = os.getenv("MIZAN_EFFORT", "high")

# URL du backend, utilisée par l'UI Streamlit.
API_URL = os.getenv("MIZAN_API_URL", "http://localhost:8000")

# max_tokens généreux : une copie multi-questions avec transcription +
# raisonnement par critère peut être longue.
MAX_TOKENS = int(os.getenv("MIZAN_MAX_TOKENS", "8000"))


def require_api_key() -> str:
    """Retourne la clé API ou lève une erreur explicite si absente."""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY manquante. Copie .env.example vers .env "
            "et renseigne ta clé, ou exporte la variable d'environnement."
        )
    return key
