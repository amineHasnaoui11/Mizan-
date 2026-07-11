# ⚖️ Mizan — correcteur de copies manuscrites

> Tunisie · K-12 · copies manuscrites **arabe + français**. L'IA propose, le prof valide (*human-in-the-loop*).

Mizan (ميزان, « la balance ») lit une photo de copie d'élève avec un VLM (Claude,
vision-first), **transcrit** ce qu'il lit, **note** critère par critère selon un
barème saisi par le prof, et produit un **feedback** bienveillant — le tout en
JSON strict. Le prof garde toujours le dernier mot.

## Décisions techniques (hackathon)

| Composant | Choix |
|---|---|
| Lecture copie | VLM vision-first (Claude) — une seule API, lit arabe **et** français |
| Notation | 100 % LLM, raisonnement critère par critère, sortie JSON stricte (*structured outputs*) |
| Référence | Option 1 (corrigé + barème saisis par le prof) ; Option 3 (raisonnement libre) en secours |
| Backend / UI | FastAPI + Streamlit |
| Human-in-the-loop | Split 2 appels : transcrire → **le prof corrige** → noter |

## Architecture

```
mizan/            cœur métier
  config.py       modèle, effort, clé API (via .env)
  schemas.py      Pydantic : référence (entrée) + correction (sortie) + JSON Schema
  prompts.py      prompts bilingues vision-first (1 appel + split)
  correcteur.py   appels Claude vision : corriger / transcrire / noter
backend/main.py   API FastAPI : /corriger, /transcrire, /noter
streamlit_app.py  UI côte à côte, human-in-the-loop
data/             exemple de référence (corrigé + barème)
```

## Démarrage

```bash
# 1. Dépendances (un venv est recommandé)
pip install -r requirements.txt

# 2. Clé API
cp .env.example .env      # puis renseigne ANTHROPIC_API_KEY

# 3. Backend (terminal 1)
uvicorn backend.main:app --reload --port 8000

# 4. UI (terminal 2)
streamlit run streamlit_app.py
```

Dans l'UI : charge l'exemple de référence, dépose une photo de copie, puis choisis
**Correction rapide** (1 appel) ou **Human-in-the-loop** (2 appels).

## Fournisseurs de modèles

Mizan supporte deux back-ends, choisis via `MIZAN_PROVIDER` :

| Provider | Lecture copie | Notation | Remarque |
|---|---|---|---|
| `anthropic` (défaut) | Claude vision-first | Claude | Le plus fort, y compris arabe manuscrit. Clé payante. |
| `esprit` | OCR (**Google Vision** / PaddleOCR) ou LLaVA | Llama 3.1 70B | Notation gratuite via la Token Factory Esprit (**réseau/VPN Esprit requis**). |

Le split human-in-the-loop est identique pour les deux : transcrire → le prof corrige → noter.

### Pipeline OCR (mode `esprit`), aligné sur le plan technique

`Photo → 1. Preprocessing (OpenCV) → 2. OCR → 3. Structuration → 4. Notation (Llama) → 5. Restitution`

La lecture de la copie est pilotée par `MIZAN_OCR` :

| `MIZAN_OCR` | Moteur | Manuscrit arabe | Setup |
|---|---|---|---|
| `google` | Google Cloud Vision | ✅ Très bon (recommandé) | Compte Google Cloud + clé JSON (`GOOGLE_APPLICATION_CREDENTIALS`), 1000 img/mois gratuites |
| `easyocr` | EasyOCR (open-source, offline) | 🟠 Correct | `pip install easyocr` — s'installe bien sur Windows |
| `paddle` | PaddleOCR (open-source, offline) | 🟠 Correct | `pip install paddleocr paddlepaddle` (wheels Windows capricieuses) |
| `llava` | LLaVA via la Token Factory | ❌ Faible | Aucun (défaut historique) |

`MIZAN_PREPROCESS=true` active le nettoyage OpenCV (deskew, binarisation, débruitage, CLAHE) — inutile avec Google Vision, utile avec PaddleOCR.

**Setup Google Cloud Vision :** console.cloud.google.com → activer l'API *Cloud Vision* → créer un *compte de service* → télécharger la clé **JSON** → `GOOGLE_APPLICATION_CREDENTIALS=chemin/vers/cle.json`.

## Configuration (.env)

| Variable | Défaut | Rôle |
|---|---|---|
| `MIZAN_PROVIDER` | `anthropic` | `anthropic` ou `esprit` |
| `MIZAN_API_URL` | `http://localhost:8000` | URL du backend vue par l'UI |
| `MIZAN_MAX_TOKENS` | `8000` | Plafond de sortie |
| **Anthropic** | | |
| `ANTHROPIC_API_KEY` | — | Clé API Anthropic |
| `MIZAN_MODEL` | `claude-opus-4-8` | Modèle vision |
| `MIZAN_EFFORT` | `high` | Effort de raisonnement (`low`→`max`) |
| **Esprit** | | |
| `ESPRIT_API_KEY` | — | Clé Token Factory |
| `MIZAN_ESPRIT_BASE_URL` | `https://tokenfactory.esprit.tn/api` | Endpoint OpenAI-compatible |
| `MIZAN_ESPRIT_VISION_MODEL` | `hosted_vllm/llava-1.5-7b-hf` | Modèle vision |
| `MIZAN_ESPRIT_TEXT_MODEL` | `hosted_vllm/Llama-3.1-70B-Instruct` | Modèle notation |
| `MIZAN_ESPRIT_VERIFY_TLS` | `false` | Vérification du certificat TLS interne |

## API

| Endpoint | Entrée | Sortie |
|---|---|---|
| `POST /corriger` | `reference` (JSON), `copie_id`, `copie` (**1..N images**), `avec_corrige` | correction complète |
| `POST /transcrire` | `reference`, `copie_id`, `copie` (**1..N images**) | transcriptions par question |
| `POST /noter` | JSON `{reference, copie_id, transcriptions}` | correction notée |

`copie` accepte **plusieurs fichiers** : dépose toutes les pages d'une même copie
et elles sont lues ensemble puis notées en une seule fois (note globale sur le
barème complet, p. ex. /20).

Exemple (copie multi-pages) :

```bash
curl -F reference="$(cat data/aziz_p1.json)" \
     -F copie_id=eleve_001 \
     -F copie=@page1.jpg \
     -F copie=@page2.jpg \
     http://localhost:8000/corriger
```

## Schéma de la référence

Voir [`data/exemple_reference.json`](data/exemple_reference.json). Chaque question
porte un `type` (`factuelle` | `qcm` | `calcul` | `ouverte`), un `corrige` et un
`bareme` où **chaque critère a une `regle` explicite** — c'est ce qui rend les
notes reproductibles d'une copie à l'autre.
