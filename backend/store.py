"""Persistance simple des devoirs (barèmes) côté serveur.

Stockage fichier JSON (data/devoirs/<id>.json) — suffisant pour le MVP et
partagé par le web et le mobile. Remplaçable par une vraie base plus tard.
"""
from __future__ import annotations

import json
import re
import secrets
from pathlib import Path

_DIR = Path(__file__).resolve().parent.parent / "data" / "devoirs"
_COPIES = Path(__file__).resolve().parent.parent / "data" / "copies"


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


# --------------------------------------------------------------------------- #
# Copies corrigées & validées — l'« espace » partagé aux élèves
# Chaque copie a un jeton unique => lien privé (un élève ne voit que la sienne).
# --------------------------------------------------------------------------- #


def enregistrer_copie(copie: dict) -> str:
    """Enregistre une copie validée et renvoie son jeton (lien privé)."""
    _COPIES.mkdir(parents=True, exist_ok=True)
    jeton = copie.get("jeton") or secrets.token_urlsafe(8)
    copie["jeton"] = jeton
    (_COPIES / f"{jeton}.json").write_text(
        json.dumps(copie, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return jeton


def charger_copie(jeton: str) -> dict | None:
    # jeton = base64-url ; on refuse tout ce qui n'est pas alphanumérique/-/_
    if not re.fullmatch(r"[A-Za-z0-9_-]+", jeton or ""):
        return None
    f = _COPIES / f"{jeton}.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def lister_copies(devoir_id: str | None = None) -> list[dict]:
    """Résumé des copies (pour l'espace prof). Filtre par devoir si fourni."""
    if not _COPIES.exists():
        return []
    out = []
    for f in sorted(_COPIES.glob("*.json")):
        try:
            c = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if devoir_id and c.get("devoir_id") != devoir_id:
            continue
        corr = c.get("correction", {})
        out.append(
            {
                "jeton": c.get("jeton", f.stem),
                "devoir_id": c.get("devoir_id", ""),
                "eleve": c.get("eleve", ""),
                "classe": c.get("classe", ""),
                "note_globale": corr.get("note_globale"),
                "note_max": corr.get("note_max"),
            }
        )
    return out
