# Mizan — Frontend (SaaS)

Interface web du produit Mizan, pensée pour les enseignant·es du primaire/secondaire
en Tunisie. SPA React branchée sur l'API FastAPI (`backend/`).

## Stack

Vite · React 18 · TypeScript (strict) · Tailwind CSS · Framer Motion · React Router ·
i18next (FR/AR + RTL) · lucide-react.

## Design system

- **Marque** vert-encre `#0E4D45` + terracotta `#E07A3F`, fond papier `#FAF7F2`.
- **Typo** Fraunces (titres) · IBM Plex Sans Arabic (UI bilingue) · IBM Plex Mono (notes).
- **Couleurs de note** (vert/ambre/rouge) séparées de la marque.
- Tokens centralisés dans `tailwind.config.ts`.

## Démarrage

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173  (proxy /api -> http://localhost:8000)
```

Lance le backend en parallèle : `uvicorn backend.main:app --reload --port 8000`.

## Structure

```
src/
  components/ui/       primitives (Button, Card, Badge)
  components/layout/   AppShell, Sidebar, Topbar, MobileNav, PageHeader
  components/brand/    BalanceMark (logo animé)
  features/            dashboard, devoirs, correction, partage, classes, settings
  lib/                 api.ts (client FastAPI), i18n.ts (FR/AR), utils.ts
  mocks/               données factices (phase visual-first)
  styles/              globals.css (Tailwind + base)
```

## Roadmap

- **Phase 0** ✅ Fondations : shell, design system, routing, i18n/RTL, dashboard mock.
- **Phase 1** Dashboard (graphiques réels).
- **Phase 2** Devoirs : éditeur barème + corrigé type.
- **Phase 3** Correction : uploader → pré-note → validation (API réelle).
- **Phase 4** Partage élèves (document classe + vue individuelle).
- **Phase 5** Classes, auth, persistance.
