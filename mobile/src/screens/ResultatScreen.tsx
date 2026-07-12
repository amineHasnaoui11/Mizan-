import { useState } from "react";
import { View, Text, StyleSheet, SafeAreaView, ScrollView, TextInput } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { colors, radius, couleurNote } from "../theme";
import { Button, Card, Badge } from "../components/UI";
import type { Correction } from "../api";
import type { RootStackParamList } from "./types";

type Props = NativeStackScreenProps<RootStackParamList, "Resultat">;

export function ResultatScreen({ route, navigation }: Props) {
  const [correction, setCorrection] = useState<Correction>(route.params.correction);
  const total = correction.questions.reduce((s, q) => s + (q.note || 0), 0);
  const totalMax = correction.questions.reduce((s, q) => s + (q.note_max || 0), 0);
  const aVerifier = correction.questions.filter((q) => q.a_verifier);

  function setNote(numero: number, val: string) {
    const note = Number(val.replace(",", ".")) || 0;
    setCorrection((c) => ({
      ...c,
      questions: c.questions.map((q) => (q.numero === numero ? { ...q, note, a_verifier: false } : q)),
    }));
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Card>
          <Text style={styles.muted}>{route.params.eleve} · note proposée (ajustable)</Text>
          <Text style={[styles.note, { color: couleurNote(total, totalMax) }]}>
            {Math.round(total * 100) / 100} <Text style={styles.noteMax}>/ {Math.round(totalMax * 100) / 100}</Text>
          </Text>
        </Card>

        {aVerifier.length > 0 && (
          <View style={styles.warn}>
            <Text style={styles.warnText}>
              ⚠️ {aVerifier.length} question(s) à vérifier ({aVerifier.map((q) => `Q${q.numero}`).join(", ")}) —
              ta décision prime.
            </Text>
          </View>
        )}

        {correction.questions.map((q) => (
          <Card key={q.numero} style={[styles.qCard, q.a_verifier && styles.qCardWarn]}>
            <View style={styles.qHead}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 8, flex: 1 }}>
                <Text style={styles.qTitle}>Question {q.numero}</Text>
                {q.a_verifier && <Badge text="à vérifier" color={colors.scorePartial} />}
              </View>
              <View style={styles.noteEdit}>
                <TextInput
                  value={String(q.note)}
                  onChangeText={(v) => setNote(q.numero, v)}
                  keyboardType="decimal-pad"
                  style={[styles.noteInput, { color: couleurNote(q.note, q.note_max) }]}
                />
                <Text style={styles.muted}> / {q.note_max}</Text>
              </View>
            </View>
            {!!q.transcription && (
              <Text style={styles.trans}>
                <Text style={styles.muted}>Lu : </Text>
                {q.transcription}
              </Text>
            )}
            {q.a_verifier && !!q.raison_doute && <Text style={styles.doute}>🤔 {q.raison_doute}</Text>}
            {!!q.feedback && <Text style={styles.feedback}>💬 {q.feedback}</Text>}
          </Card>
        ))}

        <View style={{ marginTop: 20, gap: 10 }}>
          <Button title="✓ Valider la note" onPress={() => navigation.navigate("Accueil")} />
          <Button title="Corriger une autre copie" variant="outline" onPress={() => navigation.navigate("Scan")} />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  content: { padding: 16, paddingBottom: 40 },
  muted: { color: colors.muted, fontSize: 13 },
  note: { fontSize: 40, fontWeight: "700", marginTop: 4 },
  noteMax: { fontSize: 20, color: colors.muted, fontWeight: "400" },
  warn: { backgroundColor: "#FBEFD8", borderRadius: radius.lg, padding: 12, marginTop: 12 },
  warnText: { color: colors.ink, fontSize: 14 },
  qCard: { marginTop: 12 },
  qCardWarn: { borderColor: colors.scorePartial, borderWidth: 2 },
  qHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
  qTitle: { fontSize: 16, fontWeight: "600", color: colors.ink },
  noteEdit: { flexDirection: "row", alignItems: "center" },
  noteInput: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: 10,
    width: 60,
    textAlign: "center",
    paddingVertical: 6,
    fontSize: 16,
    fontWeight: "700",
  },
  trans: { marginTop: 10, color: colors.ink, fontSize: 14, backgroundColor: colors.paper, padding: 8, borderRadius: 8 },
  doute: { marginTop: 8, color: colors.scorePartial, fontSize: 14 },
  feedback: { marginTop: 8, color: colors.muted, fontSize: 14, fontStyle: "italic" },
});
