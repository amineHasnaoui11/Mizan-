"""Jeu de données de démonstration pour le tableau de bord prof.

But : garantir qu'en démo (jury) le dashboard est **toujours rempli et fiable**,
sans dépendre d'une correction live (OCR + tunnel + LLM). On charge un devoir
réel (barème arabe « Éveil scientifique 6ème ») et on génère plusieurs copies
pré-corrigées, avec des lacunes de classe nettes et pédagogiquement crédibles.

Tout est déterministe : re-seeder donne exactement les mêmes données (démo
reproductible), et l'opération est idempotente (elle purge les anciennes copies
de démo avant de régénérer).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import store

_RACINE = Path(__file__).resolve().parent.parent
_SOURCE = _RACINE / "data" / "eveil_6eme_complet.json"

DEMO_DEVOIR_ID = "demo-eveil-6eme"

# 6 élèves fictifs (noms tunisiens plausibles) avec un facteur de niveau.
# > 1 = fort, < 1 = en difficulté. Donne une classe hétérogène réaliste.
_ELEVES = [
    ("Aziz Abdeli", "6ème B", 1.06),
    ("Mariem Trabelsi", "6ème B", 0.95),
    ("Youssef Khelifi", "6ème B", 0.70),
    ("Nour Ben Salah", "6ème B", 1.00),
    ("Rayan Gharbi", "6ème B", 0.55),
    ("Sirine Hammami", "6ème B", 0.86),
]

# Mots-clés « raisonnement » : les questions qui les contiennent sont les plus
# ratées par la classe (justifier, expliquer, montrer...). Elles deviennent les
# lacunes mises en avant par le dashboard.
_MOTS_RAISONNEMENT = ("علّل", "علل", "فسّر", "فسر", "وضّح", "وضح", "استنتج", "برهن", "لماذا")


def _jitter(eleve_i: int, numero: int) -> float:
    """Petit décalage déterministe dans [-0.08, +0.08] (pas de hasard réel)."""
    h = (eleve_i * 31 + numero * 17) % 17
    return (h - 8) / 100.0


def _questions_lacunes(ref: dict) -> set[int]:
    """Numéros des questions 'raisonnement' = les lacunes de la classe."""
    durs: set[int] = set()
    for q in ref.get("questions", []):
        enonce = q.get("enonce", "")
        if any(m in enonce for m in _MOTS_RAISONNEMENT):
            durs.add(q.get("numero"))
    # Filet de sécurité : si le barème ne matche aucun mot-clé, on prend
    # quelques questions réparties pour quand même montrer des lacunes.
    if not durs:
        numeros = [q.get("numero") for q in ref.get("questions", [])]
        durs = set(numeros[2:12:3])
    return durs


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _corriger_copie(ref: dict, eleve_i: int, facteur: float, durs: set[int]) -> dict:
    """Fabrique une correction complète (par question) pour un élève."""
    questions_corr = []
    total = 0.0
    for q in ref.get("questions", []):
        numero = q.get("numero")
        note_max = float(q.get("note_max") or 0)
        base = 0.32 if numero in durs else 0.84
        ratio = _clamp(base * facteur + _jitter(eleve_i, numero), 0.05, 1.0)
        note = round(ratio * note_max, 2)
        total += note
        difficile = numero in durs
        questions_corr.append(
            {
                "numero": numero,
                "transcription": q.get("corrige", "")[:60] or "(réponse de l'élève)",
                "note": note,
                "note_max": note_max,
                "criteres": [
                    {
                        "critere": (q.get("bareme") or [{}])[0].get("critere", "Réponse attendue"),
                        "points_obtenus": note,
                        "points_max": note_max,
                        "justification": (
                            "Raisonnement incomplet, la justification manque."
                            if difficile
                            else "Réponse conforme au corrigé."
                        ),
                    }
                ],
                "feedback": (
                    "Idée présente mais l'explication n'est pas aboutie."
                    if difficile
                    else "Bonne maîtrise de la notion."
                ),
                # Sur les questions dures, l'IA signale un doute (human-in-the-loop).
                "confiance": 0.62 if difficile else 0.94,
                "a_verifier": difficile and ratio > 0.25,
                "raison_doute": (
                    "Réponse partielle : à vérifier si l'essentiel du raisonnement y est."
                    if difficile
                    else ""
                ),
            }
        )
    note_max_dev = float(ref.get("note_max_devoir") or 0)
    eleve, classe, _ = _ELEVES[eleve_i]
    return {
        "devoir_id": DEMO_DEVOIR_ID,
        "eleve": eleve,
        "classe": classe,
        "correction": {
            "copie_id": f"demo-{eleve_i}",
            "langue_detectee": "ar",
            "note_globale": round(total, 2),
            "note_max": note_max_dev,
            "questions": questions_corr,
            "feedback_global": "Correction de démonstration (données pré-chargées).",
        },
    }


def _purger_copies_demo() -> None:
    """Supprime les copies de démo existantes (idempotence)."""
    for r in store.lister_copies(DEMO_DEVOIR_ID):
        f = store._COPIES / f"{r['jeton']}.json"
        if f.exists():
            f.unlink()


def seed() -> dict:
    """Charge le devoir de démo + ses copies. Renvoie un résumé."""
    if not _SOURCE.exists():
        raise FileNotFoundError(
            f"Barème de démo introuvable : {_SOURCE}. "
            "Vérifie data/eveil_6eme_complet.json."
        )
    ref = json.loads(_SOURCE.read_text(encoding="utf-8"))
    ref["devoir_id"] = DEMO_DEVOIR_ID
    ref.setdefault("matiere", "الإيقاظ العلمي (démo)")
    devoir_id = store.enregistrer(ref)

    _purger_copies_demo()
    # Invalide le cache d'analyse pour forcer un recalcul propre.
    _fichier_cache = _RACINE / "data" / "analyses" / f"{devoir_id}.json"
    if _fichier_cache.exists():
        _fichier_cache.unlink()

    durs = _questions_lacunes(ref)
    jetons = []
    for i, (_, _, facteur) in enumerate(_ELEVES):
        copie = _corriger_copie(ref, i, facteur, durs)
        # jeton déterministe => re-seed = mêmes liens
        copie["jeton"] = f"demo-{DEMO_DEVOIR_ID}-{i}"
        jetons.append(store.enregistrer_copie(copie))

    return {
        "devoir_id": devoir_id,
        "matiere": ref.get("matiere", ""),
        "nb_copies": len(jetons),
        "nb_lacunes": len(durs),
    }
