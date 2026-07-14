import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import type { TextStyle } from "react-native";

export type Lang = "fr" | "ar";

const T: Record<string, { fr: string; ar: string }> = {
  tagline: { fr: "L'IA propose, le prof valide.", ar: "الذكاء الاصطناعي يقترح، والأستاذ يصادق." },
  // Accueil
  home_devoirs: { fr: "📚 Mes devoirs", ar: "📚 فروضي" },
  home_exercice: { fr: "🧠 Corriger un exercice", ar: "🧠 إصلاح تمرين" },
  home_hint: {
    fr: "Devoirs : crée un barème puis note les copies. Exercice : un corrigé direct, sans devoir.",
    ar: "الفروض: أنشئ سلّماً ثم أصلح النسخ. تمرين: إصلاح مباشر دون فرض.",
  },
  home_demo: { fr: "📊 Tableau de bord (démo)", ar: "📊 لوحة القيادة (تجربة)" },
  demo_chargement: { fr: "Chargement de la démo…", ar: "جارٍ تحميل التجربة…" },
  // Titres d'écrans
  nav_devoirs: { fr: "Mes devoirs", ar: "فروضي" },
  nav_nouveau: { fr: "Nouveau devoir", ar: "فرض جديد" },
  nav_scan: { fr: "Corriger une copie", ar: "إصلاح نسخة" },
  nav_exercice: { fr: "Corriger un exercice", ar: "إصلاح تمرين" },
  nav_analyse: { fr: "Analyse de la classe", ar: "تحليل القسم" },
  nav_resultat: { fr: "Résultat", ar: "النتيجة" },
  // Communs
  eleve: { fr: "Élève", ar: "التلميذ" },
  classe: { fr: "Classe", ar: "القسم" },
  matiere: { fr: "Matière", ar: "المادة" },
  niveau: { fr: "Niveau", ar: "المستوى" },
  devoir: { fr: "Devoir", ar: "الفرض" },
  ajouter_page: { fr: "📷 Ajouter une page", ar: "📷 إضافة صفحة" },
  photo: { fr: "Photo", ar: "صورة" },
  galerie: { fr: "Galerie", ar: "المعرض" },
  // Devoirs
  nouveau_devoir: { fr: "➕ Nouveau devoir", ar: "➕ فرض جديد" },
  aucun_devoir: { fr: "Aucun devoir pour l'instant.", ar: "لا توجد فروض بعد." },
  aucun_devoir_sub: {
    fr: "Crée-en un en photographiant devoir + barème + corrigé.",
    ar: "أنشئ واحداً بتصوير الفرض + السلّم + الإصلاح.",
  },
  corriger_copie: { fr: "📷 Corriger une copie", ar: "📷 إصلاح نسخة" },
  analyse_classe: { fr: "📊 Analyse de la classe", ar: "📊 تحليل القسم" },
  questions: { fr: "questions", ar: "أسئلة" },
  // Scan
  copie_eleve: { fr: "Copie de l'élève", ar: "نسخة التلميذ" },
  lire_copie: { fr: "① Lire la copie", ar: "① قراءة النسخة" },
  lecture: { fr: "Lecture de la copie…", ar: "جارٍ قراءة النسخة…" },
  relis: { fr: "② Relis ce que l'IA a lu", ar: "② راجع ما قرأه الذكاء الاصطناعي" },
  noter: { fr: "③ Noter la copie", ar: "③ إسناد العدد" },
  notation: { fr: "Notation en cours…", ar: "جارٍ الإسناد…" },
  aucun_devoir_corriger: { fr: "Aucun devoir à corriger", ar: "لا يوجد فرض للإصلاح" },
  creer_devoir_dabord: { fr: "Crée d'abord un devoir (barème + corrigé type).", ar: "أنشئ فرضاً أولاً (سلّم + إصلاح نموذجي)." },
  aller_devoirs: { fr: "Aller aux devoirs", ar: "الذهاب إلى الفروض" },
  // Résultat
  note_ajustable: { fr: "Note proposée (ajustable)", ar: "العدد المقترح (قابل للتعديل)" },
  a_verifier: { fr: "à vérifier", ar: "للمراجعة" },
  lu: { fr: "Lu : ", ar: "قُرئ: " },
  valider_note: { fr: "✓ Valider la note", ar: "✓ المصادقة على العدد" },
  note_enregistree: { fr: "✓ Note enregistrée", ar: "✓ تم تسجيل العدد" },
  partager_classe: { fr: "🔗 Partager l'accès de la classe", ar: "🔗 مشاركة رابط القسم" },
  autre_copie: { fr: "Corriger une autre copie", ar: "إصلاح نسخة أخرى" },
  // Exercice
  ex_intro: {
    fr: "Scanne un exercice, l'IA te donne le corrigé — pas besoin de barème.",
    ar: "صوّر تمريناً، يمنحك الذكاء الاصطناعي الإصلاح — دون سلّم.",
  },
  consigne: { fr: "Consigne (facultatif)", ar: "التعليمة (اختياري)" },
  obtenir_corrige: { fr: "Obtenir le corrigé", ar: "الحصول على الإصلاح" },
  corrige: { fr: "Corrigé", ar: "الإصلاح" },
  // Analyse
  analyse_sur: { fr: "Analyse sur", ar: "تحليل على" },
  copies: { fr: "copie(s)", ar: "نسخة" },
  moyenne_reussite: { fr: "Réussite moyenne", ar: "معدل النجاح" },
  nb_lacunes: { fr: "Lacunes", ar: "نقائص" },
  reussite_question: { fr: "Réussite par question", ar: "النجاح حسب السؤال" },
  lacunes: { fr: "Lacunes principales", ar: "أهم النقائص" },
  qcm_remediation: { fr: "QCM de remédiation", ar: "أسئلة اختيارية للمعالجة" },
  astuces: { fr: "Astuces de remédiation", ar: "نصائح للمعالجة" },
  echec: { fr: "d'échec", ar: "إخفاق" },
  analyse_en_cours: { fr: "Analyse de la classe en cours…", ar: "جارٍ تحليل القسم…" },
  // Construire devoir
  construire_intro: {
    fr: "Prends en photo les documents du devoir. L'IA en construit le barème ; tu pourras le relire avant d'enregistrer.",
    ar: "صوّر وثائق الفرض. ينشئ الذكاء الاصطناعي السلّم؛ يمكنك مراجعته قبل الحفظ.",
  },
  doc_devoir: { fr: "📄 Devoir vierge", ar: "📄 الفرض الفارغ" },
  doc_devoir_hint: { fr: "les énoncés des questions", ar: "نصوص الأسئلة" },
  doc_bareme: { fr: "📊 Barème", ar: "📊 السلّم" },
  doc_bareme_hint: { fr: "les points par question", ar: "النقاط لكل سؤال" },
  doc_corrige: { fr: "✍️ Ta correction", ar: "✍️ إصلاحك" },
  doc_corrige_hint: { fr: "les réponses attendues", ar: "الإجابات المنتظرة" },
  construire_bareme: { fr: "Construire le barème", ar: "إنشاء السلّم" },
  construction: { fr: "Construction du barème…", ar: "جارٍ إنشاء السلّم…" },
  relis_bareme: { fr: "Relis et corrige si besoin (énoncé, points, corrigé), puis enregistre.", ar: "راجع وصحّح عند الحاجة (النص، النقاط، الإصلاح) ثم احفظ." },
  enregistrer_devoir: { fr: "✓ Enregistrer le devoir", ar: "✓ حفظ الفرض" },
  enregistrement: { fr: "Enregistrement…", ar: "جارٍ الحفظ…" },
};

interface Ctx {
  lang: Lang;
  dir: "ltr" | "rtl";
  setLang: (l: Lang) => void;
  t: (k: keyof typeof T) => string;
  rtlText: TextStyle;
}

const LangContext = createContext<Ctx | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("fr");
  const value = useMemo<Ctx>(
    () => ({
      lang,
      dir: lang === "ar" ? "rtl" : "ltr",
      setLang,
      t: (k) => T[k]?.[lang] ?? String(k),
      rtlText: lang === "ar" ? { writingDirection: "rtl", textAlign: "right" } : {},
    }),
    [lang],
  );
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang(): Ctx {
  const c = useContext(LangContext);
  if (!c) throw new Error("useLang hors LangProvider");
  return c;
}
