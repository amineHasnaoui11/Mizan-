# 🎯 Mizan — Fiche de défense jury

> Mémo des points sur lesquels le jury peut challenger, avec les réponses fortes.
> « Donne-moi les points jury » → ressortir ce document.

---

## 0. Pitch

**Une phrase :** *Mizan pré-corrige les copies manuscrites (arabe + français) des élèves
tunisiens : l'IA lit, propose une note critère par critère et signale ses doutes ; le
prof valide en quelques clics et partage à chaque élève sa copie corrigée.*

**30 secondes :** En Tunisie, un prof du primaire/secondaire corrige des centaines de
copies manuscrites, en arabe et en français. Mizan lit la copie (OCR), la structure par
question selon le barème et le corrigé fournis par le prof, propose une note **avec un
niveau de confiance**, et **lève la main sur les cas douteux**. Le prof reste le décideur.
Puis chaque élève reçoit **uniquement** sa copie corrigée et sa note.

---

## 1. Ce qui compte — faits & chiffres à citer

- **Pipeline aligné sur le plan technique** : Photo → 1. Prétraitement (OpenCV) →
  2. OCR → 3. Structuration → 4. Notation (LLM, critère par critère) → 5. Restitution.
- **Human-in-the-loop** : split en 2 temps — *transcrire → le prof corrige → noter*.
- **Bilingue AR + FR**, y compris **RTL complet** dans l'UI (différenciateur régional).
- **Gratuit** à ce stade : notation via **Llama 3.1 70B** (Token Factory Esprit),
  lecture via **Google Cloud Vision** (1000 img/mois gratuites). **Aucune clé payante requise.**
- **Testé sur données réelles** : copie d'Aziz Abdeli (SVT 6ème, arabe manuscrit),
  barème réel /20 reconstruit depuis l'épreuve Archipel, notation critère par critère.
- **Confiance explicite** : chaque question porte `confiance` (0→1), `a_verifier`,
  `raison_doute` → le prof relit **seulement** les cas signalés.
- **Construction du barème assistée** : le prof uploade *devoir vierge + barème + corrigé*,
  Mizan en extrait le barème structuré (éditable).
- **Multi-pages / PDF** : une copie de N pages → une note globale.

---

## 2. Questions-pièges du jury → réponses

### A. Technique / IA

**« L'OCR ne lit pas bien l'arabe manuscrit, donc c'est inutilisable. »**
→ C'est notre hypothèse-risque n°1, et le produit est **conçu autour**. Deux réponses :
(1) Google Cloud Vision lit le manuscrit arabe **nettement mieux** que l'open-source —
démontré sur la copie d'Aziz (texte cohérent, nom + réponses lus). (2) Surtout, le
**human-in-the-loop** est le filet : l'IA pré-remplit, le prof corrige la transcription en
30 s au lieu de tout retaper. On ne prétend pas à 100 % d'OCR — on prétend faire **gagner
du temps** au prof avec un dernier mot humain.

**« Comment faire confiance à une note d'IA ? »**
→ On **ne demande pas** de faire confiance aveuglément. L'IA **propose**, le prof **dispose**.
Chaque note a un **niveau de confiance** et un flag **« à vérifier »** ; le prof arbitre les
cas signalés. C'est un **copilote**, pas un pilote automatique.

**« Et les matières subjectives (rédaction, philo, éducation islamique) ? »**
→ Traitement **général** : la subjectivité pédagogique est encodée dans la **règle du
barème** (`regle`). L'IA applique la règle là où elle existe ; là où elle est muette, elle
donne un **crédit partiel prudent** + signale. Elle distingue *incomplet mais exact*
(partiel) de *complet mais erroné* (strict). Curseur « décide seule ↔ défère au prof »
selon le degré d'objectivité de la question.

**« Que se passe-t-il sur un cas limite (70 % d'un verset, méthode alternative en maths) ? »**
→ Elle **ne tranche jamais en silence** : points partiels **+** `a_verifier=true` **+** raison
du doute. Le prof décide en un clic. Règle d'or du système.

**« C'est juste un wrapper autour de ChatGPT. »**
→ Non : (1) **bilingue AR/FR + RTL** natif ; (2) **barème + corrigé structurés** (notation
reproductible d'une copie à l'autre, pas au feeling) ; (3) **auto-évaluation de confiance**
et human-in-the-loop intégrés ; (4) **pipeline OCR→structuration→notation** spécifique au
manuscrit ; (5) ciblé **K-12 Tunisie** (barèmes, langues, workflow prof). Un chatbot
généraliste ne fait aucun de ces cinq points de bout en bout.

**« Votre modèle Llama est sur le réseau Esprit uniquement. »**
→ Vrai pour le prototype (gratuit pour le hackathon). L'architecture est **découplée par
provider** (`MIZAN_PROVIDER`) : passer à un modèle hébergé (Claude, GPT, Llama managé)
= changer une variable. La logique métier ne bouge pas.

### B. Produit / adoption

**« Un prof non-technique saura-t-il l'utiliser ? »**
→ UI orientée prof : 1) Préparer le devoir (upload barème/corrigé), 2) Corriger une copie
(dépose → note). Pas de JSON en façade, langage prof, bilingue. Flux en 3 clics.

**« Les profs vont-ils accepter qu'une IA note leurs élèves ? »**
→ Justement, elle ne **note pas à leur place** : elle **pré-corrige** et fait gagner du
temps. Le prof garde l'autorité et la responsabilité. Argument d'adoption, pas de
remplacement.

**« Différenciation / concurrence ? »**
→ Peu d'outils ciblent le **manuscrit arabe K-12** avec human-in-the-loop et barème
structuré. Notre niche : Tunisie, bilingue, copies scannées, prof au centre.

### C. Données / éthique

**« Confidentialité des copies d'élèves ? »**
→ Cloisonnement : **chaque élève ne voit que SA copie et SA note**. Le prof gère son
espace. Roadmap : stockage chiffré, conformité type RGPD, hébergement maîtrisé.

**« Biais / équité de la notation ? »**
→ Barème + règles explicites = notation **reproductible** (même règle pour toutes les
copies), ce qui réduit le biais humain de fatigue/ordre. Et le prof valide. On peut auditer
les écarts IA/prof (tableau de comparaison).

**« Triche possible ? »**
→ L'élève ne note pas ; le prof valide. Le risque est côté lecture (OCR), traité par la
relecture prof.

### D. Faisabilité / passage à l'échelle

**« Ça marche vraiment ou c'est une maquette ? »**
→ Démonstration de bout en bout sur une **vraie copie manuscrite arabe** : OCR →
structuration par question → note critère par critère. Backend FastAPI + moteur OCR/LLM
fonctionnels.

**« Coût à l'échelle ? »**
→ Aujourd'hui gratuit (Esprit + palier gratuit Vision). À l'échelle : coût par copie
maîtrisable (OCR ~0,0015 $/image au-delà du gratuit ; LLM selon provider). Le batch
multi-copies et le mobile-scan amortissent le temps prof.

**« Précision vs le vrai prof ? »**
→ Honnêteté : sur Aziz, écart IA/prof dû surtout à **l'échelle du barème** (page /5,25,
pas /4,5) et à des transcriptions à compléter — pas à un raisonnement faux. Une fois le
barème calibré et la transcription validée, l'IA se rapproche du prof. Et l'écart **est le
rôle** du human-in-the-loop.

---

## 3. Nos faiblesses — assumées + parades

| Faiblesse réelle | Parade |
|---|---|
| OCR arabe manuscrit imparfait | Human-in-the-loop (relecture prof) + Google Vision |
| Modèle Llama intranet Esprit | Architecture multi-provider, bascule = 1 variable |
| Pas encore d'auth/BD (MVP) | Roadmap claire (persistance, comptes, stockage) |
| Calibration de la note | Barème précis + règles explicites + validation prof |
| Dépendance réseau/quota | Modes offline (EasyOCR) + provider configurable |

---

## 4. Vision / roadmap (si on demande « et après ? »)

- **App mobile + scan** de copie (photo → note) pour le terrain.
- **Dashboard** enseignant : moyennes, suivi, classes.
- **Partage élève** : chaque élève reçoit sa copie corrigée.
- **Persistance & comptes** (base de données, auth), conformité données.
- **Multi-provider** hébergé pour sortir du réseau Esprit.

---

## 5. Réponses-réflexes (à mémoriser mot pour mot)

- « L'IA **propose**, le prof **valide**. »
- « On ne vise pas 100 % d'OCR, on vise **faire gagner du temps** au prof. »
- « Le doute est **toujours signalé**, jamais caché. »
- « La subjectivité est dans la **règle du barème**, pas dans l'humeur du modèle. »
- « Chaque élève ne voit **que sa propre copie**. »
