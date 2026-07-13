"""Comptes élèves — authentification légère (MVP, sans dépendance externe).

Un élève se connecte avec (nom, classe, mot de passe) et voit uniquement SES
copies (celles que le prof a validées à son nom, dans sa classe).

Stockage fichier ; mots de passe hachés avec PBKDF2 (stdlib). Sessions par
jeton aléatoire persisté. Remplaçable par une vraie base + JWT plus tard.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
from pathlib import Path

_ELEVES = Path(__file__).resolve().parent.parent / "data" / "eleves"
_SESSIONS = Path(__file__).resolve().parent.parent / "data" / "sessions.json"


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _cle(name: str, classe: str) -> str:
    """Identifiant stable d'un élève = normalisation de nom + classe."""
    brut = f"{_norm(classe)}|{_norm(name)}"
    return hashlib.sha256(brut.encode("utf-8")).hexdigest()[:16]


def _fichier(cle: str) -> Path:
    return _ELEVES / f"{cle}.json"


def _hash(password: str, sel: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(sel), 100_000).hex()


# --------------------------------------------------------------------------- #
# Comptes
# --------------------------------------------------------------------------- #


def creer_eleve(name: str, classe: str, password: str) -> dict:
    if not (name.strip() and classe.strip() and password):
        raise ValueError("Nom, classe et mot de passe sont requis.")
    cle = _cle(name, classe)
    if _fichier(cle).exists():
        raise ValueError("Un compte existe déjà pour ce nom dans cette classe. Connecte-toi.")
    sel = secrets.token_hex(16)
    eleve = {
        "cle": cle,
        "name": name.strip(),
        "classe": classe.strip(),
        "sel": sel,
        "hash": _hash(password, sel),
    }
    _ELEVES.mkdir(parents=True, exist_ok=True)
    _fichier(cle).write_text(json.dumps(eleve, ensure_ascii=False, indent=2), encoding="utf-8")
    return eleve


def verifier_eleve(name: str, classe: str, password: str) -> dict | None:
    f = _fichier(_cle(name, classe))
    if not f.exists():
        return None
    eleve = json.loads(f.read_text(encoding="utf-8"))
    if secrets.compare_digest(eleve["hash"], _hash(password, eleve["sel"])):
        return eleve
    return None


# --------------------------------------------------------------------------- #
# Sessions (jeton -> clé élève)
# --------------------------------------------------------------------------- #


def _lire_sessions() -> dict:
    if _SESSIONS.exists():
        try:
            return json.loads(_SESSIONS.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def creer_session(cle: str) -> str:
    sessions = _lire_sessions()
    jeton = secrets.token_urlsafe(24)
    sessions[jeton] = cle
    _SESSIONS.parent.mkdir(parents=True, exist_ok=True)
    _SESSIONS.write_text(json.dumps(sessions, ensure_ascii=False), encoding="utf-8")
    return jeton


def eleve_de_session(jeton: str) -> dict | None:
    cle = _lire_sessions().get((jeton or "").strip())
    if not cle:
        return None
    f = _fichier(cle)
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def meme_eleve(copie: dict, eleve: dict) -> bool:
    """Une copie appartient à l'élève si nom + classe correspondent (normalisés)."""
    return _norm(copie.get("eleve", "")) == _norm(eleve["name"]) and _norm(
        copie.get("classe", "")
    ) == _norm(eleve["classe"])
