import i18n from "i18next";
import { initReactI18next } from "react-i18next";

/**
 * Bilingue FR (défaut) / AR. La direction (LTR/RTL) est appliquée sur <html>
 * par le composant qui change de langue.
 */
export const LANGS = ["fr", "ar"] as const;
export type Lang = (typeof LANGS)[number];

const resources = {
  fr: {
    translation: {
      app: { tagline: "L'IA propose, le prof valide." },
      nav: {
        dashboard: "Tableau de bord",
        devoirs: "Devoirs",
        correction: "Correction",
        partage: "Partage élèves",
        classes: "Classes",
        settings: "Paramètres",
      },
      dashboard: {
        title: "Tableau de bord",
        subtitle: "Vue d'ensemble de vos corrections",
        copies: "Copies corrigées",
        pending: "En attente de validation",
        classes: "Classes",
        avg: "Moyenne de classe",
        recent: "Corrections récentes",
        validate: "Valider",
        empty: "Aucune correction pour l'instant",
        emptyHint: "Corrige une première copie pour voir tes statistiques ici.",
      },
      devoirs: { title: "Devoirs", subtitle: "Barème et corrigé type par devoir" },
      correction: { title: "Correction", subtitle: "Déposez une copie, l'IA pré-note" },
      partage: { title: "Partage élèves", subtitle: "Chaque élève ne voit que sa copie" },
      classes: { title: "Classes & élèves", subtitle: "Gérez vos groupes" },
      settings: { title: "Paramètres", subtitle: "Compte et préférences" },
      common: { soon: "Bientôt disponible" },
    },
  },
  ar: {
    translation: {
      app: { tagline: "الذكاء الاصطناعي يقترح، والأستاذ يصادق." },
      nav: {
        dashboard: "لوحة القيادة",
        devoirs: "الفروض",
        correction: "الإصلاح",
        partage: "مشاركة التلاميذ",
        classes: "الأقسام",
        settings: "الإعدادات",
      },
      dashboard: {
        title: "لوحة القيادة",
        subtitle: "نظرة عامة على الإصلاحات",
        copies: "نسخ مُصلَحة",
        pending: "في انتظار المصادقة",
        classes: "الأقسام",
        avg: "معدل القسم",
        recent: "إصلاحات حديثة",
        validate: "مصادقة",
        empty: "لا توجد إصلاحات بعد",
        emptyHint: "أصلح أول نسخة لتظهر إحصائياتك هنا.",
      },
      devoirs: { title: "الفروض", subtitle: "السلّم والإصلاح النموذجي لكل فرض" },
      correction: { title: "الإصلاح", subtitle: "أودِع نسخة، يقترح الذكاء الاصطناعي عدداً" },
      partage: { title: "مشاركة التلاميذ", subtitle: "كل تلميذ يرى نسخته فقط" },
      classes: { title: "الأقسام والتلاميذ", subtitle: "أدِر مجموعاتك" },
      settings: { title: "الإعدادات", subtitle: "الحساب والتفضيلات" },
      common: { soon: "قريباً" },
    },
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "fr",
  fallbackLng: "fr",
  interpolation: { escapeValue: false },
});

export function appliquerDirection(lang: Lang) {
  const dir = lang === "ar" ? "rtl" : "ltr";
  document.documentElement.setAttribute("dir", dir);
  document.documentElement.setAttribute("lang", lang);
}

export default i18n;
