import { useEffect, useState } from "react";
import { View, Text, StyleSheet, SafeAreaView, ScrollView, ActivityIndicator } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { colors, couleurNote } from "../theme";
import { Card, Badge } from "../components/UI";
import { useLang } from "../i18n";
import { analyserDevoir, type AnalyseResult } from "../api";
import type { RootStackParamList } from "./types";

type Props = NativeStackScreenProps<RootStackParamList, "Analyse">;

export function AnalyseScreen({ route }: Props) {
  const { t, rtlText } = useLang();
  const [data, setData] = useState<AnalyseResult | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    analyserDevoir(route.params.devoirId)
      .then(setData)
      .catch((e) => setErreur(e instanceof Error ? e.message : String(e)));
  }, [route.params.devoirId]);

  if (erreur) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}>
          <Text style={styles.erreur}>{erreur}</Text>
        </View>
      </SafeAreaView>
    );
  }
  if (!data) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}>
          <ActivityIndicator color={colors.accent} />
          <Text style={styles.muted}>{t("analyse_en_cours")}</Text>
        </View>
      </SafeAreaView>
    );
  }

  const a = data.analyse;
  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={[styles.h1, rtlText]}>{route.params.matiere}</Text>
        <Text style={[styles.muted, rtlText]}>{t("analyse_sur")} {data.nb_copies} {t("copies")}</Text>

        {!!a.synthese && (
          <Card style={styles.card}>
            <Text style={[styles.body, rtlText]}>{a.synthese}</Text>
          </Card>
        )}

        <Text style={[styles.h2, rtlText]}>{t("reussite_question")}</Text>
        <Card style={styles.card}>
          {data.stats.map((s) => (
            <View key={s.numero} style={styles.barRow}>
              <Text style={styles.qlabel}>Q{s.numero}</Text>
              <View style={styles.barBg}>
                <View style={[styles.barFill, { width: `${s.taux_reussite}%`, backgroundColor: couleurNote(s.taux_reussite, 100) }]} />
              </View>
              <Text style={styles.pct}>{s.taux_reussite}%</Text>
            </View>
          ))}
        </Card>

        {a.lacunes?.length > 0 && (
          <>
            <Text style={[styles.h2, rtlText]}>{t("lacunes")}</Text>
            {a.lacunes.map((l, i) => (
              <Card key={i} style={styles.card}>
                <View style={styles.lacHead}>
                  <Text style={[styles.lacSujet, rtlText]}>{l.sujet}</Text>
                  <Badge text={`${l.taux_echec}% ${t("echec")}`} color={colors.scoreZero} />
                </View>
                <Text style={[styles.muted, rtlText]}>{l.explication}</Text>
                {l.questions?.length > 0 && <Text style={styles.qref}>Questions : {l.questions.map((q) => `Q${q}`).join(", ")}</Text>}
              </Card>
            ))}
          </>
        )}

        {a.qcm?.length > 0 && (
          <>
            <Text style={[styles.h2, rtlText]}>{t("qcm_remediation")}</Text>
            {a.qcm.map((q, i) => (
              <Card key={i} style={styles.card}>
                <Text style={[styles.body, rtlText]}>{q.question}</Text>
                {q.options.map((o, j) => (
                  <Text key={j} style={[styles.opt, o === q.reponse && styles.optOk, rtlText]}>
                    {o === q.reponse ? "✓ " : "• "}{o}
                  </Text>
                ))}
              </Card>
            ))}
          </>
        )}

        {a.astuces?.length > 0 && (
          <>
            <Text style={[styles.h2, rtlText]}>{t("astuces")}</Text>
            <Card style={styles.card}>
              {a.astuces.map((astuce, i) => (
                <Text key={i} style={[styles.astuce, rtlText]}>💡 {astuce}</Text>
              ))}
            </Card>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  center: { flex: 1, alignItems: "center", justifyContent: "center", gap: 10, padding: 24 },
  content: { padding: 16, paddingBottom: 40 },
  h1: { fontSize: 22, fontWeight: "700", color: colors.ink },
  h2: { fontSize: 16, fontWeight: "700", color: colors.ink, marginTop: 18, marginBottom: 4 },
  muted: { color: colors.muted, fontSize: 13 },
  body: { color: colors.ink, fontSize: 15, lineHeight: 22 },
  card: { marginTop: 8 },
  erreur: { color: colors.scoreZero, fontSize: 14, textAlign: "center" },
  barRow: { flexDirection: "row", alignItems: "center", marginVertical: 5 },
  qlabel: { width: 34, fontSize: 13, fontWeight: "600", color: colors.ink },
  barBg: { flex: 1, height: 10, backgroundColor: colors.line, borderRadius: 999, overflow: "hidden" },
  barFill: { height: 10, borderRadius: 999 },
  pct: { width: 44, textAlign: "right", fontSize: 13, color: colors.mutedStrong, fontVariant: ["tabular-nums"] },
  lacHead: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 6 },
  lacSujet: { fontSize: 15, fontWeight: "700", color: colors.ink, flex: 1 },
  qref: { marginTop: 6, fontSize: 12, color: colors.muted },
  opt: { fontSize: 14, color: colors.mutedStrong, marginTop: 6 },
  optOk: { color: colors.scoreFull, fontWeight: "700" },
  astuce: { fontSize: 14, color: colors.ink, marginTop: 6, lineHeight: 20 },
});
