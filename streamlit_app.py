"""UI Mizan — correcteur de copies, human-in-the-loop.

Deux modes de correction :
  * Rapide (1 appel)      — la photo part directement, l'IA transcrit + note.
  * Human-in-the-loop     — 1) l'IA transcrit, 2) le prof relit/corrige la
    (2 appels)               transcription, 3) l'IA note la version validée.

L'écran de résultat affiche côte à côte : la photo, la transcription (éditable)
et les critères colorés. L'argument jury : on montre ce que l'IA a LU, et le prof
garde le dernier mot.
"""
from __future__ import annotations

import json
from pathlib import Path

import requests
import streamlit as st

from mizan import config

st.set_page_config(page_title="Mizan — correcteur de copies", page_icon="⚖️", layout="wide")

API = config.API_URL
DATA = Path(__file__).parent / "data"
EXEMPLE = DATA / "exemple_reference.json"
EXEMPLE_AZIZ = DATA / "aziz_p1.json"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _charger_fichier(chemin: Path) -> str:
    if chemin.exists():
        return chemin.read_text(encoding="utf-8")
    return "{}"


def _charger_exemple() -> str:
    return _charger_fichier(EXEMPLE)


def _couleur_ratio(obtenus: float, maxi: float) -> str:
    if maxi <= 0:
        return "#9aa0a6"
    r = obtenus / maxi
    if r >= 0.999:
        return "#2e7d32"  # vert
    if r <= 0.001:
        return "#c62828"  # rouge
    return "#ef6c00"  # orange (partiel)


def _badge(texte: str, couleur: str) -> str:
    return (
        f'<span style="background:{couleur};color:white;padding:2px 8px;'
        f'border-radius:10px;font-size:0.85em;white-space:nowrap">{texte}</span>'
    )


def _afficher_correction(correction: dict, image_files) -> None:
    """Affiche la correction : photo(s) à gauche, détail par question à droite."""
    note = correction.get("note_globale", 0)
    note_max = correction.get("note_max", 0)
    st.markdown(f"### Note proposée : **{note} / {note_max}**  ·  "
                f"langue détectée : `{correction.get('langue_detectee', '?')}`")
    if correction.get("feedback_global"):
        st.info(correction["feedback_global"], icon="📝")

    col_photo, col_detail = st.columns([1, 1.4], gap="large")
    with col_photo:
        st.caption("Copie de l'élève")
        for f in image_files or []:
            st.image(f, use_container_width=True)

    with col_detail:
        for q in correction.get("questions", []):
            couleur = _couleur_ratio(q.get("note", 0), q.get("note_max", 0))
            st.markdown(
                f"**Question {q.get('numero')}** &nbsp; "
                + _badge(f"{q.get('note', 0)} / {q.get('note_max', 0)}", couleur),
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                st.caption("Transcription (ce que l'IA a lu)")
                st.write(q.get("transcription", "") or "_—_")
                for c in q.get("criteres", []):
                    c_col = _couleur_ratio(c.get("points_obtenus", 0), c.get("points_max", 0))
                    st.markdown(
                        _badge(
                            f"{c.get('points_obtenus', 0)}/{c.get('points_max', 0)}",
                            c_col,
                        )
                        + f" &nbsp; **{c.get('critere', '')}**",
                        unsafe_allow_html=True,
                    )
                    st.caption(c.get("justification", ""))
                if q.get("feedback"):
                    st.markdown(f"💬 _{q['feedback']}_")


def _telecharger(correction: dict, copie_id: str) -> None:
    st.download_button(
        "⬇️ Télécharger la correction (JSON)",
        data=json.dumps(correction, ensure_ascii=False, indent=2),
        file_name=f"correction_{copie_id}.json",
        mime="application/json",
    )


# --------------------------------------------------------------------------- #
# Barre latérale : référence + copie
# --------------------------------------------------------------------------- #

st.title("⚖️ Mizan — correcteur de copies")
st.caption(
    f"Arabe + français manuscrits · l'IA propose, le prof valide "
    f"· fournisseur : **{config.PROVIDER}**"
)
if config.PROVIDER == "esprit":
    _lecteur = {
        "google": "Google Cloud Vision (OCR)",
        "easyocr": "EasyOCR",
        "paddle": "PaddleOCR",
        "llava": "LLaVA (vision)",
    }.get(config.OCR, config.OCR)
    st.caption(
        f"ℹ️ Mode Esprit : **{_lecteur}** transcrit, Llama 3.1 70B note. "
        "Relis toujours la transcription avant de noter (human-in-the-loop)."
    )

with st.sidebar:
    st.header("1. Référence (corrigé + barème)")
    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        if st.button("Exemple SVT (fr)", use_container_width=True):
            st.session_state["reference_txt"] = _charger_exemple()
    with col_ex2:
        if st.button("Copie arabe (Aziz)", use_container_width=True,
                     help="Barème réel — SVT 6ème, sang/nutrition, en arabe."):
            st.session_state["reference_txt"] = _charger_fichier(EXEMPLE_AZIZ)
    reference_txt = st.text_area(
        "JSON de référence",
        value=st.session_state.get("reference_txt", _charger_exemple()),
        height=280,
        key="reference_txt",
    )

    st.header("2. Copie de l'élève")
    copie_id = st.text_input("copie_id", value="eleve_001")
    image_files = st.file_uploader(
        "Photos de la copie (plusieurs pages possibles)",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        help="Ajoute toutes les pages d'une même copie : elles seront lues "
        "ensemble et notées en une seule fois.",
    )
    if image_files:
        st.caption(f"📄 {len(image_files)} page(s) chargée(s)")

    st.header("3. Options")
    avec_corrige = st.checkbox(
        "Utiliser le corrigé fourni", value=True,
        help="Décoche pour l'Option 3 (raisonnement libre, sans corrigé).",
    )

try:
    reference = json.loads(reference_txt) if reference_txt.strip() else {}
except json.JSONDecodeError as e:
    st.sidebar.error(f"Référence JSON invalide : {e}")
    reference = None


# --------------------------------------------------------------------------- #
# Onglets : mode rapide vs human-in-the-loop
# --------------------------------------------------------------------------- #

onglet_rapide, onglet_hitl = st.tabs(
    ["⚡ Correction rapide (1 appel)", "🧑‍🏫 Human-in-the-loop (2 appels)"]
)

# ---- Mode rapide ---------------------------------------------------------- #
with onglet_rapide:
    st.write("La/les photo(s) partent directement : l'IA transcrit **et** note en une passe.")
    pret = reference and image_files
    if st.button("Corriger la copie", type="primary", disabled=not pret):
        with st.spinner("Correction en cours…"):
            resp = requests.post(
                f"{API}/corriger",
                data={
                    "reference": json.dumps(reference, ensure_ascii=False),
                    "copie_id": copie_id,
                    "avec_corrige": str(avec_corrige).lower(),
                },
                files=[
                    ("copie", (f.name, f.getvalue(), f.type)) for f in image_files
                ],
                timeout=300,
            )
        if resp.ok:
            correction = resp.json()
            st.success("Correction proposée — à valider par l'enseignant.")
            _afficher_correction(correction, image_files)
            _telecharger(correction, copie_id)
        else:
            st.error(f"Erreur {resp.status_code} : {resp.text}")
    elif not pret:
        st.info("Renseigne une référence valide et charge au moins une photo de copie.")

# ---- Mode human-in-the-loop ---------------------------------------------- #
with onglet_hitl:
    st.write(
        "**Étape 1** — l'IA lit la copie. **Étape 2** — tu relis/corriges la "
        "transcription. **Étape 3** — l'IA note la version que tu as validée."
    )
    pret = reference and image_files

    if st.button("Étape 1 — Transcrire la copie", disabled=not pret):
        with st.spinner("Lecture de la copie…"):
            resp = requests.post(
                f"{API}/transcrire",
                data={
                    "reference": json.dumps(reference, ensure_ascii=False),
                    "copie_id": copie_id,
                },
                files=[
                    ("copie", (f.name, f.getvalue(), f.type)) for f in image_files
                ],
                timeout=300,
            )
        if resp.ok:
            st.session_state["transcriptions"] = resp.json().get("transcriptions", [])
            st.session_state["hitl_copie_id"] = copie_id
        else:
            st.error(f"Erreur {resp.status_code} : {resp.text}")

    transcriptions = st.session_state.get("transcriptions")
    if transcriptions:
        st.divider()
        col_photo, col_edit = st.columns([1, 1.4], gap="large")
        with col_photo:
            st.caption("Copie de l'élève")
            for f in image_files or []:
                st.image(f, use_container_width=True)
        with col_edit:
            st.caption("Étape 2 — relis et corrige la transcription")
            corrigees = []
            for t in transcriptions:
                num = t.get("numero")
                txt = st.text_area(
                    f"Question {num}",
                    value=t.get("transcription", ""),
                    key=f"trans_{num}",
                    height=100,
                )
                corrigees.append({"numero": num, "transcription": txt})

            if st.button("Étape 3 — Noter la version validée", type="primary"):
                with st.spinner("Notation en cours…"):
                    resp = requests.post(
                        f"{API}/noter",
                        json={
                            "reference": reference,
                            "copie_id": st.session_state.get("hitl_copie_id", copie_id),
                            "transcriptions": corrigees,
                        },
                        timeout=180,
                    )
                if resp.ok:
                    correction = resp.json()
                    st.success("Note proposée à partir de la transcription validée.")
                    _afficher_correction(correction, image_files)
                    _telecharger(correction, correction.get("copie_id", copie_id))
                else:
                    st.error(f"Erreur {resp.status_code} : {resp.text}")
