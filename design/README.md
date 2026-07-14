# Mizan · ميزان — Identité visuelle & maquettes

**Fichier : [`mizan-maquettes.html`](./mizan-maquettes.html)** — ouvrir dans un navigateur.
Document autonome (~2,8 Mo) : polices embarquées en data-URI, aucun réseau requis.

Promesse produit : **« L'IA propose, le prof valide. »**
Direction artistique : *cahier d'école soigné* — papier chaud, encre d'ardoise, terracotta.
Bilingue par conception : chaque écran existe en **français (LTR)** et en **arabe (RTL, miroir natif
via propriétés CSS logiques)**.

## Contenu

1. **Style tile** — palette de marque + sémantique de note (deux systèmes séparés), typographie
   en situation FR/AR, boutons, badges de note, badge « à vérifier », motif balance animé,
   formes & ombres.
2. **App mobile prof (6 écrans)** — Accueil · Mes devoirs · Nouveau devoir (3 scans → barème IA
   éditable) · Corriger une copie · Résultat (note héros + doutes signalés) · Analyse de classe.
3. **Portail élève (2 écrans)** — Connexion · Ma copie corrigée (feedback bienveillant).
4. **Avant / après** — la valeur : 4 h 05 → 38 min, 100 % des doutes montrés au prof.
5. **Bonus** — landing page marketing (héro bilingue, problème/solution, 3 features, CTA).

## Tokens

| Rôle | Valeur |
|---|---|
| Vert-encre (marque) | `#0E4D45` |
| Terracotta (action) | `#E07A3F` |
| Papier chaud (fond) | `#FAF7F2` |
| Surface / Ligne | `#FFFFFF` / `#E9E2D8` |
| Note réussie / partielle / échec | `#2E7D32` / `#E8A13A` / `#C0442E` |
| Titres | Fraunces 600 (latin) · Plex Sans Arabic 700 (arabe) |
| UI & corps | IBM Plex Sans Arabic 400/500/700 |
| Notes & chiffres | IBM Plex Mono 500/600, `tabular-nums` |
| Rayons / ombres | 10–20 px · ombres basses teintées brun chaud |

## Règles clés

- Le **terracotta** porte une seule action par écran ; il ne sert jamais à alerter.
- Les couleurs de **note** ne sont jamais utilisées par la marque — le rouge garde son sens.
- Le doute IA (« à vérifier ») est **ambre doux** : raison en clair, extrait de copie,
  champ pré-rempli — une main levée, pas une alarme.
- Motif signature : la **balance qui s'équilibre** (oscille puis se pose, ressort léger 3,2 s ;
  immobile si `prefers-reduced-motion`).
- La note se **compte sous les yeux** (compteur animé, IBM Plex Mono).
