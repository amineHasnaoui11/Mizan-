"""UI Mizan — correcteur de copies, pensé pour l'enseignant.

Deux temps, comme le travail réel d'un prof :

  1. 📋 Préparer le devoir — le prof fournit le **barème** et le **corrigé type**
     (la réponse attendue par question). C'est la référence sur laquelle l'IA
     s'appuie pour noter.
  2. ✍️ Corriger une copie — dépose la copie de l'élève (photos ou PDF),
     l'IA lit, le prof relit/valide, l'IA note. Le prof garde le dernier mot.

Le JSON reste accessible dans un volet « Avancé », mais l'enseignant n'en a
pas besoin au quotidien.
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
EXEMPLE_COMPLET = DATA / "eveil_6eme_complet.json"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _charger_fichier(chemin: Path) -> str:
    if chemin.exists():
        return chemin.read_text(encoding="utf-8")
    return "{}"


def _reference_courante() -> tuple[dict | None, str]:
    """Parse la référence stockée en session ; (None, txt) si JSON invalide."""
    txt = st.session_state.get("reference_txt", "")
    if not txt.strip():
        return {}, txt
    try:
        return json.loads(txt), txt
    except json.JSONDecodeError:
        return None, txt


def _total_points(reference: dict) -> float:
    return round(sum(q.get("note_max", 0) for q in reference.get("questions", [])), 3)


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


def _est_pdf(f) -> bool:
    return (f.type or "") == "application/pdf" or (f.name or "").lower().endswith(".pdf")


def _apercu_fichiers(files) -> None:
    """Affiche les pages de la copie (images directes, PDF rendus page par page)."""
    for f in files or []:
        if _est_pdf(f):
            try:
                import fitz  # PyMuPDF

                doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                for page in doc:
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4))
                    st.image(pix.tobytes("png"), use_container_width=True)
            except Exception:
                st.info(f"📄 {f.name} (PDF — aperçu indisponible)")
        else:
            st.image(f, use_container_width=True)


def _afficher_correction(correction: dict, image_files) -> None:
    """Affiche la correction : photo(s) à gauche, détail par question à droite."""
    note = correction.get("note_globale", 0)
    note_max = correction.get("note_max", 0)
    couleur = _couleur_ratio(note, note_max)
    st.markdown(
        f"## Note proposée : {_badge(f'{note} / {note_max}', couleur)}",
        unsafe_allow_html=True,
    )
    st.caption(f"langue détectée : {correction.get('langue_detectee', '?')} · à valider par l'enseignant")
    if correction.get("feedback_global"):
        st.info(correction["feedback_global"], icon="📝")

    col_photo, col_detail = st.columns([1, 1.4], gap="large")
    with col_photo:
        st.caption("Copie de l'élève")
        _apercu_fichiers(image_files)

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
# En-tête + barre latérale (infos seulement)
# --------------------------------------------------------------------------- #

st.title("⚖️ Mizan — correcteur de copies")
st.caption("Arabe + français manuscrits · l'IA propose, le prof valide.")

with st.sidebar:
    st.markdown("### ⚖️ Mizan")
    st.caption(f"Fournisseur : **{config.PROVIDER}**")
    if config.PROVIDER == "esprit":
        _lecteur = {
            "google": "Google Cloud Vision (OCR)",
            "easyocr": "EasyOCR",
            "paddle": "PaddleOCR",
            "llava": "LLaVA (vision)",
        }.get(config.OCR, config.OCR)
        st.caption(f"Lecture : **{_lecteur}** · Notation : Llama 3.1 70B")
    st.divider()
    st.caption(
        "**Comment ça marche**\n\n"
        "1. Prépare le devoir : barème + corrigé type.\n"
        "2. Corrige une copie : dépose-la, relis ce que l'IA a lu, note.\n\n"
        "Tu gardes toujours le dernier mot."
    )

# Référence par défaut au premier chargement.
if "reference_txt" not in st.session_state:
    st.session_state["reference_txt"] = _charger_fichier(EXEMPLE_AZIZ)


# --------------------------------------------------------------------------- #
# Onglets principaux
# --------------------------------------------------------------------------- #

tab_prep, tab_corr = st.tabs(["📋 Préparer le devoir", "✍️ Corriger une copie"])


# =========================================================================== #
# ONGLET 1 — Préparer le devoir (barème + corrigé type)
# =========================================================================== #

with tab_prep:
    st.subheader("Barème & corrigé type")
    st.write(
        "Charge un devoir existant ou saisis le tien : l'IA notera les copies "
        "en s'appuyant sur **ce barème et ce corrigé**."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Exemple SVT (fr)", use_container_width=True):
            st.session_state["reference_txt"] = _charger_fichier(EXEMPLE)
            st.rerun()
    with c2:
        if st.button("Situation 1 · sang (ar)", use_container_width=True,
                     help="Barème réel — Éveil scientifique 6ème, situation 1, /7."):
            st.session_state["reference_txt"] = _charger_fichier(EXEMPLE_AZIZ)
            st.rerun()
    with c3:
        if st.button("Épreuve complète /20 (ar)", use_container_width=True,
                     help="Barème complet des 3 situations — copie entière (PDF multi-pages)."):
            st.session_state["reference_txt"] = _charger_fichier(EXEMPLE_COMPLET)
            st.rerun()

    reference, _ = _reference_courante()

    if reference is None:
        st.error("Le barème (JSON) est invalide. Corrige-le dans le volet « Avancé » ci-dessous.")
    elif not reference.get("questions"):
        st.info("Aucune question. Charge un exemple ci-dessus ou saisis un barème dans « Avancé ».")
    else:
        questions = reference.get("questions", [])
        total = _total_points(reference)
        st.success(
            f"**{reference.get('matiere', 'Devoir')}** · {reference.get('niveau', '')} · "
            f"**{len(questions)} questions** · total **{total} pts**"
        )
        st.caption(
            "Pour chaque question : l'énoncé, les points, et le **corrigé type** "
            "(réponse attendue). Édite le corrigé si besoin, puis enregistre."
        )

        devoir_id = reference.get("devoir_id", "devoir")
        with st.form("form_corrige"):
            nouveaux = {}
            for q in questions:
                num = q.get("numero")
                pts = q.get("note_max", 0)
                typ = q.get("type", "ouverte")
                with st.container(border=True):
                    st.markdown(
                        f"**Q{num}** · " + _badge(f"{pts} pts", "#37474f")
                        + f" &nbsp; _{typ}_",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**Énoncé :** {q.get('enonce', '')}")
                    nouveaux[num] = st.text_area(
                        f"Réponse attendue (corrigé) — Q{num}",
                        value=q.get("corrige", ""),
                        key=f"corr_{devoir_id}_{num}",
                        height=90,
                    )
                    criteres = q.get("bareme", [])
                    if criteres:
                        st.caption(
                            "Critères : "
                            + " · ".join(
                                f"{c.get('critere', '')} ({c.get('points_max', 0)})"
                                for c in criteres
                            )
                        )
            enregistrer = st.form_submit_button("💾 Enregistrer le corrigé", type="primary")

        if enregistrer:
            for q in reference["questions"]:
                q["corrige"] = nouveaux.get(q.get("numero"), q.get("corrige", ""))
            st.session_state["reference_txt"] = json.dumps(
                reference, ensure_ascii=False, indent=2
            )
            st.success("Corrigé type enregistré. Passe à l'onglet « Corriger une copie ».")
            st.rerun()

    with st.expander("⚙️ Avancé — éditer le barème complet (JSON)"):
        st.caption("Format libre. Chaque question : numero, enonce, type, corrige, note_max, bareme[].")
        st.text_area("JSON de référence", key="reference_txt", height=320)


# =========================================================================== #
# ONGLET 2 — Corriger une copie
# =========================================================================== #

with tab_corr:
    reference, _ = _reference_courante()

    if not reference or not reference.get("questions"):
        st.warning(
            "Prépare d'abord un barème dans l'onglet **📋 Préparer le devoir**."
        )
    else:
        st.subheader("Copie de l'élève")
        st.caption(
            f"Devoir : **{reference.get('matiere', '')}** · "
            f"{len(reference.get('questions', []))} questions · "
            f"{_total_points(reference)} pts"
        )

        col_id, col_up = st.columns([1, 2])
        with col_id:
            copie_id = st.text_input("Identifiant de la copie", value="eleve_001")
        with col_up:
            image_files = st.file_uploader(
                "Photos ou PDF (plusieurs pages possibles)",
                type=["jpg", "jpeg", "png", "webp", "pdf"],
                accept_multiple_files=True,
                help="Dépose toutes les pages d'une même copie : elles sont lues "
                "ensemble et notées en une seule fois.",
            )
            if image_files:
                st.caption(f"📄 {len(image_files)} fichier(s) chargé(s)")

        with st.expander("Options"):
            avec_corrige = st.checkbox(
                "Utiliser le corrigé type (recommandé)", value=True,
                help="Décoche pour laisser l'IA raisonner librement, sans corrigé.",
            )

        pret = bool(image_files)
        st.divider()

        sous_hitl, sous_rapide = st.tabs(
            ["🧑‍🏫 Avec relecture (recommandé)", "⚡ Correction rapide"]
        )

        # ---- Avec relecture (human-in-the-loop) ----------------------------- #
        with sous_hitl:
            st.write(
                "**1.** l'IA lit la copie · **2.** tu relis/corriges ce qu'elle a lu · "
                "**3.** l'IA note la version validée."
            )
            if st.button("① Transcrire la copie", disabled=not pret):
                with st.spinner("Lecture de la copie…"):
                    resp = requests.post(
                        f"{API}/transcrire",
                        data={
                            "reference": json.dumps(reference, ensure_ascii=False),
                            "copie_id": copie_id,
                        },
                        files=[("copie", (f.name, f.getvalue(), f.type)) for f in image_files],
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
                    _apercu_fichiers(image_files)
                with col_edit:
                    st.caption("② Relis et corrige ce que l'IA a lu")
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

                    if st.button("③ Noter la version validée", type="primary"):
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

        # ---- Correction rapide (1 appel) ------------------------------------ #
        with sous_rapide:
            st.write("La copie part directement : l'IA transcrit **et** note en une passe.")
            if st.button("Corriger la copie", type="primary", disabled=not pret):
                with st.spinner("Correction en cours…"):
                    resp = requests.post(
                        f"{API}/corriger",
                        data={
                            "reference": json.dumps(reference, ensure_ascii=False),
                            "copie_id": copie_id,
                            "avec_corrige": str(avec_corrige).lower(),
                        },
                        files=[("copie", (f.name, f.getvalue(), f.type)) for f in image_files],
                        timeout=300,
                    )
                if resp.ok:
                    correction = resp.json()
                    st.success("Correction proposée — à valider par l'enseignant.")
                    _afficher_correction(correction, image_files)
                    _telecharger(correction, copie_id)
                else:
                    st.error(f"Erreur {resp.status_code} : {resp.text}")

            if not pret:
                st.info("Charge au moins une photo/page de copie ci-dessus.")
