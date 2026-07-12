"""Persistance simple des devoirs (barèmes) côté serveur.

Stockage fichier JSON (data/devoirs/<id>.json) — suffisant pour le MVP et
partagé par le web et le mobile. Remplaçable par une vraie base plus tard.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_DIR = Path(__file__).resolve().parent.parent / "data" / "devoirs"


def _slug(texte: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", texte.lower()).strip("-")
    return s or "devoir"


def _fichier(devoir_id: str) -> Path:
    # empêche toute évasion de répertoire
    nom = _slug(devoir_id)
    return _DIR / f"{nom}.json"


def lister() -> list[dict]:
    """Résumé de chaque devoir (sans le détail des questions)."""
    if not _DIR.exists():
        return []
    out = []
    for f in sorted(_DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        out.append(
            {
                "devoir_id": d.get("devoir_id", f.stem),
                "matiere": d.get("matiere", ""),
                "niveau": d.get("niveau", ""),
                "note_max_devoir": d.get("note_max_devoir", 0),
                "nb_questions": len(d.get("questions", [])),
            }
        )
    return out


def charger(devoir_id: str) -> dict | None:
    f = _fichier(devoir_id)
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def enregistrer(reference: dict) -> str:
    _DIR.mkdir(parents=True, exist_ok=True)
    devoir_id = _slug(reference.get("devoir_id", "") or reference.get("matiere", "devoir"))
    reference["devoir_id"] = devoir_id
    _fichier(devoir_id).write_text(
        json.dumps(reference, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return devoir_id


def supprimer(devoir_id: str) -> bool:
    f = _fichier(devoir_id)
    if f.exists():
        f.unlink()
        return True
    return False
