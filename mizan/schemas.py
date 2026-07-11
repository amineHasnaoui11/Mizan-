"""Schémas Pydantic : la référence saisie par le prof (entrée) et la
correction produite par l'IA (sortie).

Le schéma de sortie sert aussi de JSON Schema pour les *structured outputs*
de l'API Claude — d'où `build_output_json_schema()`, qui garantit que le
modèle renvoie toujours un JSON valide et conforme.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Référence (Option 1 : corrigé + barème saisis par le prof)
# --------------------------------------------------------------------------- #

TypeQuestion = Literal["factuelle", "qcm", "calcul", "ouverte"]
Langue = Literal["fr", "ar", "mixte"]


class CritereBareme(BaseModel):
    critere: str = Field(..., description="Ce qui est évalué")
    points_max: float
    regle: str = Field(
        ...,
        description="Règle explicite d'attribution — rend les notes reproductibles",
    )


class QuestionReference(BaseModel):
    numero: int
    enonce: str
    type: TypeQuestion = "ouverte"
    corrige: str = ""
    note_max: float
    bareme: list[CritereBareme]


class Reference(BaseModel):
    devoir_id: str
    matiere: str = ""
    niveau: str = ""
    langue: Langue = "mixte"
    note_max_devoir: float
    questions: list[QuestionReference]


# --------------------------------------------------------------------------- #
# Sortie de correction (ce que l'IA propose, ce que le prof valide)
# --------------------------------------------------------------------------- #

ReferenceUtilisee = Literal["corrige_manuel", "rag_cours", "raisonnement_libre"]


class CritereEvalue(BaseModel):
    critere: str
    points_obtenus: float
    points_max: float
    justification: str


class QuestionCorrigee(BaseModel):
    numero: int
    transcription: str = Field(
        ..., description="Ce que l'IA a lu — clé pour la transparence et l'édition prof"
    )
    reference_utilisee: ReferenceUtilisee = "corrige_manuel"
    note: float
    note_max: float
    criteres: list[CritereEvalue]
    feedback: str


class Correction(BaseModel):
    copie_id: str
    langue_detectee: Langue = "mixte"
    note_globale: float
    note_max: float
    questions: list[QuestionCorrigee]
    feedback_global: str


# --------------------------------------------------------------------------- #
# JSON Schema pour structured outputs (strict, sans contraintes non supportées)
# --------------------------------------------------------------------------- #


def build_reference_json_schema() -> dict:
    """JSON Schema de la référence (barème) — pour guider la construction LLM."""
    critere = {
        "type": "object",
        "properties": {
            "critere": {"type": "string"},
            "points_max": {"type": "number"},
            "regle": {"type": "string"},
        },
        "required": ["critere", "points_max", "regle"],
    }
    question = {
        "type": "object",
        "properties": {
            "numero": {"type": "integer"},
            "enonce": {"type": "string"},
            "type": {"type": "string", "enum": ["factuelle", "qcm", "calcul", "ouverte"]},
            "corrige": {"type": "string"},
            "note_max": {"type": "number"},
            "bareme": {"type": "array", "items": critere},
        },
        "required": ["numero", "enonce", "type", "corrige", "note_max", "bareme"],
    }
    return {
        "type": "object",
        "properties": {
            "devoir_id": {"type": "string"},
            "matiere": {"type": "string"},
            "niveau": {"type": "string"},
            "langue": {"type": "string", "enum": ["fr", "ar", "mixte"]},
            "note_max_devoir": {"type": "number"},
            "questions": {"type": "array", "items": question},
        },
        "required": ["devoir_id", "note_max_devoir", "questions"],
    }


def build_output_json_schema() -> dict:
    """JSON Schema conforme aux structured outputs Claude.

    Toutes les propriétés sont `required` et `additionalProperties: false`,
    comme l'exige l'API. On n'utilise aucune contrainte non supportée
    (minLength, minimum, etc.).
    """
    critere = {
        "type": "object",
        "properties": {
            "critere": {"type": "string"},
            "points_obtenus": {"type": "number"},
            "points_max": {"type": "number"},
            "justification": {"type": "string"},
        },
        "required": ["critere", "points_obtenus", "points_max", "justification"],
        "additionalProperties": False,
    }
    question = {
        "type": "object",
        "properties": {
            "numero": {"type": "integer"},
            "transcription": {"type": "string"},
            "reference_utilisee": {
                "type": "string",
                "enum": ["corrige_manuel", "rag_cours", "raisonnement_libre"],
            },
            "note": {"type": "number"},
            "note_max": {"type": "number"},
            "criteres": {"type": "array", "items": critere},
            "feedback": {"type": "string"},
        },
        "required": [
            "numero",
            "transcription",
            "reference_utilisee",
            "note",
            "note_max",
            "criteres",
            "feedback",
        ],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {
            "copie_id": {"type": "string"},
            "langue_detectee": {"type": "string", "enum": ["fr", "ar", "mixte"]},
            "note_globale": {"type": "number"},
            "note_max": {"type": "number"},
            "questions": {"type": "array", "items": question},
            "feedback_global": {"type": "string"},
        },
        "required": [
            "copie_id",
            "langue_detectee",
            "note_globale",
            "note_max",
            "questions",
            "feedback_global",
        ],
        "additionalProperties": False,
    }
