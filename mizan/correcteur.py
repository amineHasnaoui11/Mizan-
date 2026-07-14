"""Dispatcher de fournisseur.

Expose les trois fonctions métier (corriger_copie, transcrire_copie,
noter_transcription) et route vers le bon backend selon MIZAN_PROVIDER :
  * "anthropic" -> Claude vision-first (llm_anthropic)
  * "esprit"    -> LLaVA + Llama via la Token Factory (llm_esprit)

Le backend FastAPI et l'UI n'ont pas à connaître le fournisseur : ils
importent simplement `correcteur`.
"""
from __future__ import annotations

from . import config

# esprit et groq partagent le même client OpenAI-compatible (llm_esprit).
if config.PROVIDER in ("esprit", "groq"):
    from . import llm_esprit as _impl
else:
    from . import llm_anthropic as _impl

corriger_copie = _impl.corriger_copie
transcrire_copie = _impl.transcrire_copie
noter_transcription = _impl.noter_transcription
construire_reference = _impl.construire_reference
assistant_libre = _impl.assistant_libre
analyser_lacunes = _impl.analyser_lacunes

__all__ = [
    "corriger_copie",
    "transcrire_copie",
    "noter_transcription",
    "construire_reference",
    "assistant_libre",
    "analyser_lacunes",
]
