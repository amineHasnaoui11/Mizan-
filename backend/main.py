"""API FastAPI de Mizan.

Endpoints :
  GET  /              — santé / infos
  POST /corriger      — 1 appel : image + référence -> correction complète
  POST /transcrire    — split étape 1 : image -> transcriptions par question
  POST /noter         — split étape 2 : transcriptions validées -> correction

La référence est passée en champ de formulaire `reference` (JSON stringifié),
l'image en fichier `copie`. Cela permet un upload multipart simple depuis
Streamlit ou curl.
"""
from __future__ import annotations

import json

import html as _html

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ValidationError

from mizan import __version__, config, correcteur
from mizan.schemas import Reference

from . import auth, store

app = FastAPI(title="Mizan API", version=__version__)

_MEDIA_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
}
_PDF_TYPES = {"application/pdf", "application/x-pdf"}
# On vise ~2200 px sur le grand côté : assez pour l'OCR manuscrit, sans
# produire des images énormes (limite Google Vision ~20 Mo/image).
_PDF_MAX_COTE = 2200


def _pdf_to_images(data: bytes) -> list[tuple[bytes, str]]:
    """Rend chaque page d'un PDF en JPEG (une image par page), taille bornée."""
    try:
        import fitz  # PyMuPDF, import paresseux
    except ImportError as e:  # pragma: no cover
        raise HTTPException(
            500,
            "Lecture PDF indisponible : installe PyMuPDF (pip install pymupdf).",
        ) from e
    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        raise HTTPException(400, f"PDF illisible : {e}") from e
    pages: list[tuple[bytes, str]] = []
    for page in doc:
        cote = max(page.rect.width, page.rect.height) or 1
        zoom = min(2.0, _PDF_MAX_COTE / cote)  # jamais plus de 2x
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        pages.append((pix.tobytes("jpeg"), "image/jpeg"))
    if not pages:
        raise HTTPException(400, "PDF sans page.")
    return pages


def _parse_reference(reference_str: str) -> dict:
    try:
        data = json.loads(reference_str)
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"Référence JSON invalide : {e}") from e
    try:
        Reference.model_validate(data)  # validation de structure
    except ValidationError as e:
        raise HTTPException(422, f"Référence non conforme au schéma : {e}") from e
    return data


async def _read_fichier(copie: UploadFile) -> list[tuple[bytes, str]]:
    """Lit un fichier uploadé -> liste de (bytes, media_type).

    Une image -> une entrée. Un PDF -> une entrée par page.
    """
    media_type = copie.content_type or "image/jpeg"
    nom = (copie.filename or "").lower()
    data = await copie.read()
    if not data:
        raise HTTPException(400, "Fichier vide.")
    if media_type in _PDF_TYPES or nom.endswith(".pdf"):
        return _pdf_to_images(data)
    if media_type not in _MEDIA_TYPES:
        raise HTTPException(
            415,
            f"Type non supporté : {media_type}. "
            f"Attendus : {', '.join(sorted(_MEDIA_TYPES))}, application/pdf.",
        )
    return [(data, media_type)]


async def _read_images(copies: list[UploadFile]) -> list[tuple[bytes, str]]:
    """Lit toutes les pages d'une copie (images et/ou PDF multi-pages)."""
    if not copies:
        raise HTTPException(400, "Aucun fichier fourni.")
    images: list[tuple[bytes, str]] = []
    for c in copies:
        images.extend(await _read_fichier(c))
    return images


def _handle_anthropic_errors(fn):
    """Convertit les erreurs API en réponses HTTP lisibles."""
    try:
        return fn()
    except RuntimeError as e:  # clé API manquante
        raise HTTPException(500, str(e)) from e
    except Exception as e:  # erreurs SDK Anthropic, parsing, etc.
        raise HTTPException(502, f"Erreur du modèle : {e}") from e


@app.get("/")
def racine() -> dict:
    return {
        "service": "Mizan",
        "version": __version__,
        "provider": config.PROVIDER,
        "ocr": config.OCR,
        "modele_texte": config.LLM_TEXT_MODEL if config.PROVIDER in ("esprit", "groq") else config.MODEL,
        "effort": config.EFFORT,
        "endpoints": ["/construire-reference", "/corriger", "/transcrire", "/noter", "/assistant"],
    }


@app.post("/corriger")
async def corriger(
    reference: str = Form(...),
    copie_id: str = Form(...),
    copie: list[UploadFile] = File(...),
    avec_corrige: bool = Form(True),
) -> dict:
    """1 appel : image(s) + référence -> correction complète.

    `copie` accepte plusieurs fichiers = les pages d'une même copie.
    """
    ref = _parse_reference(reference)
    images = await _read_images(copie)
    resultat = _handle_anthropic_errors(
        lambda: correcteur.corriger_copie(
            ref, images, copie_id, avec_corrige=avec_corrige
        )
    )
    return resultat.model_dump()


@app.post("/transcrire")
async def transcrire(
    reference: str = Form(...),
    copie_id: str = Form(...),
    copie: list[UploadFile] = File(...),
) -> dict:
    """Split étape 1 : image(s) -> transcriptions par question (à relire).

    `copie` accepte plusieurs fichiers = les pages d'une même copie.
    """
    ref = _parse_reference(reference)
    images = await _read_images(copie)
    return _handle_anthropic_errors(
        lambda: correcteur.transcrire_copie(ref, images, copie_id)
    )


@app.post("/construire-reference")
async def construire_reference(
    devoir: list[UploadFile] = File(default=[]),
    bareme: list[UploadFile] = File(default=[]),
    corrige: list[UploadFile] = File(default=[]),
    matiere: str = Form(""),
    niveau: str = Form(""),
    langue: str = Form("mixte"),
    devoir_id: str = Form(""),
) -> dict:
    """Construit le barème structuré à partir des documents du prof.

    `devoir` (énoncés vierges), `bareme` (points), `corrige` (réponses attendues)
    acceptent chacun plusieurs fichiers (images ou PDF). Retourne une référence
    éditable par le prof avant de noter les copies.
    """
    devoir_imgs = await _read_images(devoir) if devoir else []
    bareme_imgs = await _read_images(bareme) if bareme else []
    corrige_imgs = await _read_images(corrige) if corrige else []
    if not (devoir_imgs or bareme_imgs or corrige_imgs):
        raise HTTPException(400, "Fournis au moins un document (devoir, barème ou corrigé).")
    return _handle_anthropic_errors(
        lambda: correcteur.construire_reference(
            devoir_imgs, bareme_imgs, corrige_imgs,
            matiere=matiere, niveau=niveau, langue=langue, devoir_id=devoir_id,
        )
    )


def _couleur_note(obtenus, maxi) -> str:
    try:
        r = float(obtenus) / float(maxi)
    except (TypeError, ZeroDivisionError, ValueError):
        return "#7C8B86"
    if r >= 0.999:
        return "#2E7D32"
    if r <= 0.001:
        return "#C0442E"
    return "#E8A13A"


def _page_eleve_html(c: dict) -> str:
    """Page lecture seule : note + corrections. L'élève ne voit que SA copie."""
    esc = _html.escape
    corr = c.get("correction", {})
    langue = corr.get("langue_detectee", "mixte")
    direction = "rtl" if langue == "ar" else "ltr"
    note = corr.get("note_globale", 0)
    note_max = corr.get("note_max", 0)
    eleve = esc(c.get("eleve", "Élève"))
    devoir = esc(c.get("devoir_id", ""))

    lignes = []
    for q in corr.get("questions", []):
        coul = _couleur_note(q.get("note", 0), q.get("note_max", 0))
        trans = esc(q.get("transcription", "") or "—")
        fb = esc(q.get("feedback", "") or "")
        crit = "".join(
            f'<div class="crit"><span class="pts" style="background:{_couleur_note(cr.get("points_obtenus",0), cr.get("points_max",0))}">'
            f'{esc(str(cr.get("points_obtenus",0)))}/{esc(str(cr.get("points_max",0)))}</span> {esc(cr.get("critere",""))}</div>'
            for cr in q.get("criteres", [])
        )
        lignes.append(
            f'<div class="q"><div class="qhead"><b>Question {esc(str(q.get("numero","")))}</b>'
            f'<span class="note" dir="ltr" style="color:{coul}">{esc(str(q.get("note",0)))} / {esc(str(q.get("note_max",0)))}</span></div>'
            f'<div class="trans">{trans}</div>{crit}'
            + (f'<div class="fb">💬 {fb}</div>' if fb else "")
            + "</div>"
        )

    coul_g = _couleur_note(note, note_max)
    fb_g = esc(corr.get("feedback_global", "") or "")
    return f"""<!doctype html><html lang="{esc(langue)}" dir="{direction}"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ma copie — {eleve}</title>
<style>
:root{{--ink:#0E4D45;--accent:#E07A3F;--paper:#FAF7F2;--line:#E9E2D8;--muted:#7C8B86}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);
font-family:-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.5}}
.wrap{{max-width:680px;margin:0 auto;padding:20px}}
.head{{display:flex;align-items:center;gap:8px;margin-bottom:16px}}
.brand{{font-weight:700;font-size:20px}}
.card{{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;margin-bottom:14px}}
.big{{font-size:40px;font-weight:800;font-family:ui-monospace,monospace}}
.small{{color:var(--muted);font-size:14px}}
.q .qhead{{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}}
.note{{font-family:ui-monospace,monospace;font-weight:700}}
.trans{{background:var(--paper);border-radius:10px;padding:8px 10px;margin:6px 0;font-size:14px}}
.crit{{font-size:14px;margin:4px 0}}
.pts{{color:#fff;border-radius:999px;padding:1px 8px;font-size:12px;margin-inline-end:6px;direction:ltr;display:inline-block}}
.big{{direction:ltr}} .note{{direction:ltr}}
.fb{{font-style:italic;color:var(--muted);font-size:14px;margin-top:6px}}
.foot{{text-align:center;color:var(--muted);font-size:12px;margin-top:20px}}
</style></head><body><div class="wrap">
<div class="head"><span>⚖️</span><span class="brand">Mizan</span></div>
<div class="card">
  <div class="small">{eleve}{(" · " + esc(c.get("classe",""))) if c.get("classe") else ""} · {devoir}</div>
  <div class="big" dir="ltr" style="color:{coul_g}">{esc(str(note))} <span class="small">/ {esc(str(note_max))}</span></div>
  {f'<div class="small" style="margin-top:6px">📝 {fb_g}</div>' if fb_g else ""}
</div>
{"".join(lignes)}
<div class="foot">Corrigé validé par l'enseignant · Mizan</div>
</div></body></html>"""


_PORTAIL_HTML = """<!doctype html><html lang="fr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Mizan — mes notes</title>
<style>
:root{--ink:#0E4D45;--accent:#E07A3F;--paper:#FAF7F2;--line:#E9E2D8;--muted:#7C8B86}
*{box-sizing:border-box} body{margin:0;background:var(--paper);color:var(--ink);
font-family:-apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:520px;margin:0 auto;padding:22px}
.brand{display:flex;align-items:center;gap:8px;font-weight:800;font-size:22px;margin-bottom:18px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;margin-bottom:14px}
label{display:block;font-size:13px;color:var(--muted);margin:10px 0 4px}
input{width:100%;padding:12px;border:1px solid var(--line);border-radius:12px;font-size:15px}
button{width:100%;padding:13px;border:0;border-radius:12px;background:var(--accent);color:#fff;
font-size:15px;font-weight:600;margin-top:14px;cursor:pointer}
.link{background:none;color:var(--muted);font-weight:400;margin-top:8px}
.err{color:#C0442E;font-size:14px;margin-top:10px}
.copie{display:flex;justify-content:space-between;align-items:center;border:1px solid var(--line);
border-radius:12px;padding:12px 14px;margin-top:10px;text-decoration:none;color:var(--ink)}
.note{font-family:ui-monospace,monospace;font-weight:700}
.small{color:var(--muted);font-size:13px}
h2{font-size:18px;margin:0 0 4px}
.hidden{display:none}
</style></head><body><div class="wrap">
<div class="brand">⚖️ Mizan</div>

<div id="auth" class="card">
  <h2 id="titre">Se connecter</h2>
  <div class="small">Accède à tes notes.</div>
  <label>Nom et prénom</label><input id="name" autocomplete="name">
  <label>Classe</label><input id="classe" placeholder="ex : 6ème B">
  <label>Mot de passe</label><input id="password" type="password" autocomplete="current-password">
  <div id="err" class="err"></div>
  <button id="go">Se connecter</button>
  <button id="toggle" class="link">Pas encore de compte ? Créer un compte</button>
</div>

<div id="board" class="hidden">
  <div class="card">
    <h2 id="hello"></h2>
    <div class="small" id="sub"></div>
    <button id="logout" class="link" style="background:none;color:var(--accent);text-align:left;padding:0;margin-top:10px">Se déconnecter</button>
  </div>
  <div id="copies"></div>
  <div id="vide" class="small hidden">Aucune copie pour l'instant. Reviens après la correction.</div>
</div>

<script>
var API="";var mode="login";var TK="mizan.eleve.token";
var $=function(id){return document.getElementById(id)};
$("classe").value="__CLASSE__";
function setMode(m){mode=m;
  $("titre").textContent=m==="login"?"Se connecter":"Créer mon compte";
  $("go").textContent=m==="login"?"Se connecter":"Créer mon compte";
  $("toggle").textContent=m==="login"?"Pas encore de compte ? Créer un compte":"J'ai déjà un compte — se connecter";
  $("err").textContent="";}
$("toggle").onclick=function(){setMode(mode==="login"?"register":"login")};
$("go").onclick=async function(){
  $("err").textContent="";
  var body={name:$("name").value,classe:$("classe").value,password:$("password").value};
  try{
    var r=await fetch(API+"/eleves/"+(mode==="login"?"login":"register"),
      {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)});
    if(!r.ok){$("err").textContent=(await r.json()).detail||"Erreur";return;}
    var d=await r.json();localStorage.setItem(TK,d.token);show(d);
  }catch(e){$("err").textContent="Réseau indisponible.";}
};
$("logout").onclick=function(){localStorage.removeItem(TK);location.reload();};
function show(d){$("auth").classList.add("hidden");$("board").classList.remove("hidden");
  $("hello").textContent="Bonjour "+d.name;$("sub").textContent=d.classe;loadCopies();}
async function loadCopies(){
  var t=localStorage.getItem(TK);
  var r=await fetch(API+"/eleves/copies",{headers:{Authorization:"Bearer "+t}});
  if(!r.ok){localStorage.removeItem(TK);location.reload();return;}
  var list=await r.json();var box=$("copies");box.innerHTML="";
  if(!list.length){$("vide").classList.remove("hidden");return;}
  list.forEach(function(c){
    var a=document.createElement("a");a.className="copie";a.href=c.lien;
    a.innerHTML='<span>'+(c.devoir_id||"Devoir")+'</span><span class="note">'+c.note_globale+' / '+c.note_max+'</span>';
    box.appendChild(a);
  });
}
(function(){var t=localStorage.getItem(TK);if(t){
  fetch(API+"/eleves/copies",{headers:{Authorization:"Bearer "+t}}).then(function(r){
    if(r.ok){$("auth").classList.add("hidden");$("board").classList.remove("hidden");loadCopies();}
  });}})();
</script></div></body></html>"""


def _page_portail_html(classe: str) -> str:
    return _PORTAIL_HTML.replace("__CLASSE__", _html.escape(classe or "", quote=True))


class CopiePayload(BaseModel):
    devoir_id: str = ""
    eleve: str = ""
    classe: str = ""
    correction: dict


@app.post("/copies")
def enregistrer_copie(payload: CopiePayload, request: Request) -> dict:
    """Enregistre une copie validée dans l'espace → renvoie son lien privé."""
    jeton = store.enregistrer_copie(payload.model_dump())
    lien = str(request.base_url).rstrip("/") + f"/partage/{jeton}"
    return {"jeton": jeton, "lien": lien}


@app.get("/copies")
def lister_copies(devoir_id: str | None = None) -> list[dict]:
    """Espace prof : liste des copies validées (filtrable par devoir)."""
    return store.lister_copies(devoir_id)


@app.get("/copies/{jeton}")
def obtenir_copie(jeton: str) -> dict:
    c = store.charger_copie(jeton)
    if c is None:
        raise HTTPException(404, "Copie introuvable.")
    return c


@app.get("/partage/{jeton}", response_class=HTMLResponse)
def page_partage(jeton: str) -> str:
    """Page élève (lecture seule) : l'élève ne voit QUE sa copie."""
    c = store.charger_copie(jeton)
    if c is None:
        raise HTTPException(404, "Lien invalide ou expiré.")
    return _page_eleve_html(c)


# --------------------------------------------------------------------------- #
# Comptes élèves — un seul lien de classe, chaque élève voit SES copies
# --------------------------------------------------------------------------- #


class ElevePayload(BaseModel):
    name: str
    classe: str
    password: str


@app.post("/eleves/register")
def eleve_register(p: ElevePayload) -> dict:
    try:
        eleve = auth.creer_eleve(p.name, p.classe, p.password)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"token": auth.creer_session(eleve["cle"]), "name": eleve["name"], "classe": eleve["classe"]}


@app.post("/eleves/login")
def eleve_login(p: ElevePayload) -> dict:
    eleve = auth.verifier_eleve(p.name, p.classe, p.password)
    if eleve is None:
        raise HTTPException(401, "Nom, classe ou mot de passe incorrect.")
    return {"token": auth.creer_session(eleve["cle"]), "name": eleve["name"], "classe": eleve["classe"]}


def _eleve_courant(authorization: str | None) -> dict:
    jeton = (authorization or "").removeprefix("Bearer ").strip()
    eleve = auth.eleve_de_session(jeton)
    if eleve is None:
        raise HTTPException(401, "Session invalide. Reconnecte-toi.")
    return eleve


@app.get("/eleves/copies")
def eleve_copies(request: Request, authorization: str | None = Header(None)) -> list[dict]:
    """Les copies de l'élève connecté (nom + classe correspondants)."""
    eleve = _eleve_courant(authorization)
    base = str(request.base_url).rstrip("/")
    out = []
    for c in store.lister_copies():
        full = store.charger_copie(c["jeton"])
        if full and auth.meme_eleve(full, eleve):
            out.append(
                {
                    "jeton": c["jeton"],
                    "devoir_id": c.get("devoir_id", ""),
                    "note_globale": c.get("note_globale"),
                    "note_max": c.get("note_max"),
                    "lien": f"{base}/partage/{c['jeton']}",
                }
            )
    return out


@app.get("/portail", response_class=HTMLResponse)
def portail(classe: str = "") -> str:
    """Portail élève : login/inscription puis liste de ses copies."""
    return _page_portail_html(classe)


@app.post("/assistant")
async def assistant(
    copie: list[UploadFile] = File(...),
    consigne: str = Form(""),
) -> dict:
    """Mode assistant libre : scanne un exercice, renvoie un corrigé (sans devoir)."""
    images = await _read_images(copie)
    texte = _handle_anthropic_errors(lambda: correcteur.assistant_libre(images, consigne))
    return {"texte": texte}


@app.get("/devoirs")
def lister_devoirs() -> list[dict]:
    """Résumé des devoirs enregistrés (partagé web + mobile)."""
    return store.lister()


@app.get("/devoirs/{devoir_id}")
def obtenir_devoir(devoir_id: str) -> dict:
    ref = store.charger(devoir_id)
    if ref is None:
        raise HTTPException(404, "Devoir introuvable.")
    return ref


@app.post("/devoirs")
def enregistrer_devoir(reference: dict) -> dict:
    """Enregistre (ou met à jour) un devoir. Le corps est une référence."""
    try:
        Reference.model_validate(reference)
    except ValidationError as e:
        raise HTTPException(422, f"Référence non conforme : {e}") from e
    devoir_id = store.enregistrer(reference)
    return {"devoir_id": devoir_id, "ok": True}


@app.delete("/devoirs/{devoir_id}")
def supprimer_devoir(devoir_id: str) -> dict:
    return {"supprime": store.supprimer(devoir_id)}


def _stats_devoir(reference: dict, copies: list[dict]) -> list[dict]:
    """Taux de réussite/échec par question, agrégés sur les copies de la classe."""
    enonces = {q.get("numero"): q.get("enonce", "") for q in reference.get("questions", [])}
    agg: dict = {}
    for c in copies:
        for q in c.get("correction", {}).get("questions", []):
            nm = q.get("note_max") or 0
            if nm <= 0:
                continue
            ratio = (q.get("note") or 0) / nm
            a = agg.setdefault(
                q.get("numero"),
                {"numero": q.get("numero"), "enonce": enonces.get(q.get("numero"), ""), "somme": 0.0, "nb": 0, "echecs": 0},
            )
            a["somme"] += ratio
            a["nb"] += 1
            if ratio < 0.5:
                a["echecs"] += 1
    stats = []
    for n in sorted(agg, key=lambda x: (x is None, x)):
        a = agg[n]
        stats.append(
            {
                "numero": n,
                "enonce": a["enonce"],
                "taux_reussite": round(a["somme"] / a["nb"] * 100),
                "taux_echec": round(a["echecs"] / a["nb"] * 100),
                "nb_eleves": a["nb"],
            }
        )
    return stats


def _fallback_analyse(ref: dict, stats: list[dict], nb_copies: int) -> dict:
    """Analyse déterministe SANS LLM, dérivée des stats.

    Filet de sécurité : garantit que le dashboard s'affiche toujours (démo),
    même si le modèle est indisponible (Groq/tunnel down, timeout). On prend les
    questions les plus ratées comme lacunes et on propose une remédiation générique.
    """
    pires = sorted(stats, key=lambda s: s.get("taux_echec", 0), reverse=True)
    lacunes = [
        {
            "sujet": (s.get("enonce") or f"Question {s['numero']}")[:80],
            "questions": [s["numero"]],
            "taux_echec": s.get("taux_echec", 0),
            "explication": (
                f"{s.get('taux_echec', 0)}% des élèves ont échoué sur cette question. "
                "Elle demande un raisonnement à structurer davantage."
            ),
        }
        for s in pires[:3]
        if s.get("taux_echec", 0) >= 40
    ]
    moy = round(sum(s.get("taux_reussite", 0) for s in stats) / len(stats)) if stats else 0
    sujet_principal = lacunes[0]["sujet"] if lacunes else "les notions clés"
    return {
        "synthese": (
            f"Sur {nb_copies} copies, la classe réussit en moyenne à {moy}%. "
            + (
                f"La difficulté principale porte sur : {sujet_principal}."
                if lacunes
                else "Les résultats sont homogènes, pas de lacune majeure détectée."
            )
        ),
        "lacunes": lacunes,
        "qcm": [
            {
                "question": f"Pour progresser sur « {sujet_principal} », quelle démarche adopter ?",
                "options": [
                    "Justifier chaque réponse par une preuve du document",
                    "Recopier l'énoncé",
                    "Répondre par oui ou non sans expliquer",
                ],
                "reponse": "Justifier chaque réponse par une preuve du document",
                "cible": sujet_principal,
            }
        ]
        if lacunes
        else [],
        "astuces": [
            "Reprendre en classe les questions de raisonnement (justifier, expliquer).",
            "Faire verbaliser aux élèves l'étape « pourquoi » avant d'écrire la réponse.",
            "Proposer des exercices courts ciblés sur les questions les plus ratées.",
        ],
    }


@app.post("/demo/seed")
def demo_seed() -> dict:
    """Charge un devoir de démo + copies pré-corrigées (dashboard toujours prêt).

    Idempotent : régénère les mêmes données à chaque appel. Sert à garantir une
    démo fiable sans dépendre d'une correction live.
    """
    from . import demo_seed as _seed

    return _seed.seed()


@app.get("/devoirs/{devoir_id}/analyse")
def analyser_devoir(devoir_id: str, refresh: bool = False) -> dict:
    """Dashboard prof : lacunes de la classe + QCM et astuces de remédiation.

    Résultat mis en cache (clé = nb de copies). `?refresh=1` force le recalcul.
    Si le modèle échoue, on retombe sur une analyse déterministe (jamais d'erreur
    en démo).
    """
    ref = store.charger(devoir_id)
    if ref is None:
        raise HTTPException(404, "Devoir introuvable.")
    copies = [store.charger_copie(r["jeton"]) for r in store.lister_copies(devoir_id)]
    copies = [c for c in copies if c]
    if not copies:
        raise HTTPException(400, "Aucune copie corrigée pour ce devoir. Corrige des copies d'abord.")
    stats = _stats_devoir(ref, copies)

    if not refresh:
        cache = store.charger_analyse(devoir_id, len(copies))
        if cache is not None:
            return {"nb_copies": len(copies), "stats": stats, "analyse": cache}

    try:
        analyse = correcteur.analyser_lacunes(ref, stats, len(copies))
    except Exception:
        # Modèle indisponible / lent : le dashboard reste fonctionnel.
        analyse = _fallback_analyse(ref, stats, len(copies))

    store.enregistrer_analyse(devoir_id, len(copies), analyse)
    return {"nb_copies": len(copies), "stats": stats, "analyse": analyse}


class NoterPayload(BaseModel):
    reference: dict
    copie_id: str
    transcriptions: list[dict]


@app.post("/noter")
async def noter(payload: NoterPayload) -> dict:
    """Split étape 2 : transcriptions (validées par le prof) -> correction notée."""
    try:
        Reference.model_validate(payload.reference)
    except ValidationError as e:
        raise HTTPException(422, f"Référence non conforme : {e}") from e
    resultat = _handle_anthropic_errors(
        lambda: correcteur.noter_transcription(
            payload.reference, payload.transcriptions, payload.copie_id
        )
    )
    return resultat.model_dump()
