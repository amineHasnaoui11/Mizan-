import { useState } from "react";
import { View, Text, StyleSheet, SafeAreaView, ScrollView, TextInput } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { colors, radius } from "../theme";
import { Button, Card } from "../components/UI";
import { useLang } from "../i18n";
import { PagesPicker } from "../components/PagesPicker";
import {
  construireReference,
  enregistrerDevoir,
  type ImagePage,
  type Reference,
  type QuestionReference,
} from "../api";
import type { RootStackParamList } from "./types";

type Props = NativeStackScreenProps<RootStackParamList, "NouveauDevoir">;

export function NouveauDevoirScreen({ navigation }: Props) {
  const { t, rtlText } = useLang();
  const [matiere, setMatiere] = useState("");
  const [niveau, setNiveau] = useState("");
  const [devoir, setDevoir] = useState<ImagePage[]>([]);
  const [bareme, setBareme] = useState<ImagePage[]>([]);
  const [corrige, setCorrige] = useState<ImagePage[]>([]);
  const [ref, setRef] = useState<Reference | null>(null);
  const [statut, setStatut] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  const peut = devoir.length + bareme.length + corrige.length > 0;
  const total = ref?.questions.reduce((s, q) => s + (q.note_max || 0), 0) ?? 0;

  async function construire() {
    setErreur(null);
    setStatut(t("construction"));
    try {
      setRef(await construireReference({ devoir, bareme, corrige, matiere, niveau }));
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e));
    } finally {
      setStatut(null);
    }
  }

  function majQ(q: QuestionReference) {
    if (!ref) return;
    setRef({ ...ref, questions: ref.questions.map((x) => (x.numero === q.numero ? q : x)) });
  }

  async function enregistrer() {
    if (!ref) return;
    setStatut(t("enregistrement"));
    try {
      await enregistrerDevoir({ ...ref, note_max_devoir: Math.round(total * 100) / 100 });
      navigation.goBack();
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e));
      setStatut(null);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        {!ref ? (
          <>
            <Text style={[styles.intro, rtlText]}>{t("construire_intro")}</Text>
            <Card>
              <TextInput value={matiere} onChangeText={setMatiere} placeholder={t("matiere")} placeholderTextColor={colors.muted} style={[styles.input, rtlText]} />
              <TextInput value={niveau} onChangeText={setNiveau} placeholder={t("niveau")} placeholderTextColor={colors.muted} style={[styles.input, { marginTop: 10 }, rtlText]} />
            </Card>
            <Card style={{ marginTop: 12 }}>
              <PagesPicker label={t("doc_devoir")} hint={t("doc_devoir_hint")} pages={devoir} onChange={setDevoir} />
            </Card>
            <Card style={{ marginTop: 12 }}>
              <PagesPicker label={t("doc_bareme")} hint={t("doc_bareme_hint")} pages={bareme} onChange={setBareme} />
            </Card>
            <Card style={{ marginTop: 12 }}>
              <PagesPicker label={t("doc_corrige")} hint={t("doc_corrige_hint")} pages={corrige} onChange={setCorrige} />
            </Card>

            {erreur && <Text style={styles.erreur}>{erreur}</Text>}
            <View style={{ marginTop: 16 }}>
              <Button title={t("construire_bareme")} onPress={construire} disabled={!peut || statut !== null} loading={statut !== null} />
            </View>
          </>
        ) : (
          <>
            <View style={styles.headRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.title}>{ref.matiere || "Devoir"}</Text>
                <Text style={styles.sub}>{ref.questions.length} questions · {Math.round(total * 100) / 100} pts</Text>
              </View>
            </View>
            <Text style={[styles.intro, rtlText]}>{t("relis_bareme")}</Text>
            {ref.questions.map((q) => (
              <Card key={q.numero} style={{ marginTop: 10 }}>
                <View style={styles.qHead}>
                  <Text style={styles.qNum}>Q{q.numero}</Text>
                  <View style={styles.ptsRow}>
                    <TextInput
                      value={String(q.note_max)}
                      onChangeText={(v) => majQ({ ...q, note_max: Number(v.replace(",", ".")) || 0 })}
                      keyboardType="decimal-pad"
                      style={styles.pts}
                    />
                    <Text style={styles.sub}> pts</Text>
                  </View>
                </View>
                <TextInput value={q.enonce} onChangeText={(v) => majQ({ ...q, enonce: v })} placeholder="Énoncé" placeholderTextColor={colors.muted} style={styles.input} multiline />
                <TextInput value={q.corrige} onChangeText={(v) => majQ({ ...q, corrige: v })} placeholder="Réponse attendue (corrigé)" placeholderTextColor={colors.muted} style={[styles.input, { marginTop: 8 }]} multiline />
              </Card>
            ))}
            {erreur && <Text style={styles.erreur}>{erreur}</Text>}
            <View style={{ marginTop: 16 }}>
              <Button title={t("enregistrer_devoir")} onPress={enregistrer} loading={statut !== null} />
            </View>
          </>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  content: { padding: 16, paddingBottom: 40 },
  intro: { color: colors.muted, fontSize: 14, marginBottom: 12 },
  input: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: 12,
    fontSize: 15,
    color: colors.ink,
    backgroundColor: colors.surface,
  },
  erreur: { color: colors.scoreZero, marginTop: 14, fontSize: 14 },
  headRow: { flexDirection: "row", alignItems: "center" },
  title: { fontSize: 20, fontWeight: "700", color: colors.ink },
  sub: { fontSize: 13, color: colors.muted },
  qHead: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", marginBottom: 8 },
  qNum: { fontSize: 15, fontWeight: "700", color: colors.ink },
  ptsRow: { flexDirection: "row", alignItems: "center" },
  pts: { borderWidth: 1, borderColor: colors.line, borderRadius: 8, width: 56, textAlign: "center", paddingVertical: 5, fontSize: 15, fontWeight: "700", color: colors.ink },
});
