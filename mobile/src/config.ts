/**
 * URL du backend Mizan vu depuis le téléphone.
 *
 * ⚠️ IMPORTANT : le téléphone n'est PAS "localhost". Mets ici l'IP LAN de ton
 * PC (celui qui fait tourner `uvicorn ... :8000`), par ex. http://192.168.1.15:8000
 *   - Windows : `ipconfig` → "Adresse IPv4".
 *   - Le téléphone et le PC doivent être sur le MÊME Wi-Fi.
 */
export const API_BASE = "http://192.168.1.10:8000";
