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

## Configuration (.env)

| Variable | Défaut | Rôle |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Clé API Anthropic (obligatoire) |
| `MIZAN_MODEL` | `claude-opus-4-8` | Modèle vision |
| `MIZAN_EFFORT` | `high` | Effort de raisonnement (`low`→`max`) |
| `MIZAN_API_URL` | `http://localhost:8000` | URL du backend vue par l'UI |
| `MIZAN_MAX_TOKENS` | `8000` | Plafond de sortie |

## API

| Endpoint | Entrée | Sortie |
|---|---|---|
| `POST /corriger` | `reference` (JSON), `copie_id`, `copie` (image), `avec_corrige` | correction complète |
| `POST /transcrire` | `reference`, `copie_id`, `copie` | transcriptions par question |
| `POST /noter` | JSON `{reference, copie_id, transcriptions}` | correction notée |

Exemple :

```bash
curl -F reference="$(cat data/exemple_reference.json)" \
     -F copie_id=eleve_001 \
     -F copie=@copie.jpg \
     http://localhost:8000/corriger
```

## Schéma de la référence

Voir [`data/exemple_reference.json`](data/exemple_reference.json). Chaque question
porte un `type` (`factuelle` | `qcm` | `calcul` | `ouverte`), un `corrige` et un
`bareme` où **chaque critère a une `regle` explicite** — c'est ce qui rend les
notes reproductibles d'une copie à l'autre.
