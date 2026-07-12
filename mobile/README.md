# Mizan — App mobile (Expo / React Native)

Scanner une copie d'élève avec le téléphone → l'IA pré-note → le prof valide.
Partage le backend FastAPI et les barèmes avec l'app web.

## Stack
Expo (React Native) · TypeScript · React Navigation · expo-image-picker (caméra).

## Prérequis
- Node.js installé.
- L'app **Expo Go** sur ton téléphone (App Store / Play Store).
- Le **backend** qui tourne sur ton PC : `uvicorn backend.main:app --reload --port 8000 --host 0.0.0.0`
  (note le `--host 0.0.0.0` pour être joignable depuis le téléphone).
- Téléphone et PC sur le **même Wi-Fi**.

## Configuration (important)
Édite `src/config.ts` et mets l'**IP LAN de ton PC** :
```ts
export const API_BASE = "http://192.168.1.XX:8000";
```
Trouve-la avec `ipconfig` (Windows) → « Adresse IPv4 ».

## Lancer
```bash
cd mobile
npm install
npm start
```
Un QR code s'affiche → scanne-le avec **Expo Go** → l'app s'ouvre sur ton téléphone.

## Flux
1. **Accueil** → « Scanner une copie ».
2. **Scan** → choisis un devoir (chargé depuis le backend), saisis l'élève,
   prends une photo par page, « Corriger ».
3. **Résultat** → note proposée, questions « à vérifier » surlignées, tu ajustes
   les points, « Valider ».

## Structure
```
App.tsx              navigation
src/
  config.ts          URL du backend (à éditer)
  theme.ts           couleurs Mizan
  api.ts             client API (devoirs, transcrire, noter)
  components/UI.tsx   Button, Card, Badge
  screens/           Accueil, Scan, Resultat
```

## À venir
- Chargement des polices (Fraunces / IBM Plex).
- Recadrage/scan auto du document.
- Mode hors-ligne + file d'attente.
