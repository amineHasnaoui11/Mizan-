import { useState } from "react";
import { View, Text, StyleSheet, SafeAreaView, TouchableOpacity } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { colors } from "../theme";
import { Button } from "../components/UI";
import { useLang } from "../i18n";
import { chargerDemo } from "../api";
import type { RootStackParamList } from "./types";

type Props = NativeStackScreenProps<RootStackParamList, "Accueil">;

export function AccueilScreen({ navigation }: Props) {
  const { t, lang, setLang, rtlText } = useLang();
  const [demoEnCours, setDemoEnCours] = useState(false);
  const [demoErreur, setDemoErreur] = useState<string | null>(null);

  const ouvrirDemo = async () => {
    setDemoErreur(null);
    setDemoEnCours(true);
    try {
      const d = await chargerDemo();
      navigation.navigate("Analyse", { devoirId: d.devoir_id, matiere: d.matiere });
    } catch (e) {
      setDemoErreur(e instanceof Error ? e.message : String(e));
    } finally {
      setDemoEnCours(false);
    }
  };
  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <View style={styles.top}>
          <View style={styles.switch}>
            {(["fr", "ar"] as const).map((l) => (
              <TouchableOpacity key={l} onPress={() => setLang(l)} style={[styles.chip, lang === l && styles.chipOn]}>
                <Text style={[styles.chipTxt, lang === l && styles.chipTxtOn]}>{l.toUpperCase()}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <View style={styles.brand}>
          <Text style={styles.logo}>⚖️</Text>
          <Text style={styles.title}>Mizan</Text>
          <Text style={[styles.tagline, rtlText]}>{t("tagline")}</Text>
        </View>

        <View style={styles.cta}>
          <Button title={t("home_devoirs")} onPress={() => navigation.navigate("Devoirs")} />
          <Button title={t("home_exercice")} variant="outline" onPress={() => navigation.navigate("Exercice")} />
          <Button
            title={demoEnCours ? t("demo_chargement") : t("home_demo")}
            variant="outline"
            onPress={ouvrirDemo}
            disabled={demoEnCours}
          />
          {demoErreur && <Text style={[styles.erreur, rtlText]}>{demoErreur}</Text>}
          <Text style={[styles.hint, rtlText]}>{t("home_hint")}</Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  container: { flex: 1, justifyContent: "space-between", padding: 24, paddingBottom: 40 },
  top: { flexDirection: "row", justifyContent: "flex-end", paddingTop: 8 },
  switch: { flexDirection: "row", backgroundColor: colors.surface, borderRadius: 999, borderWidth: 1, borderColor: colors.line, padding: 3 },
  chip: { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 999 },
  chipOn: { backgroundColor: colors.ink },
  chipTxt: { fontSize: 12, fontWeight: "700", color: colors.muted },
  chipTxtOn: { color: colors.paper },
  brand: { flex: 1, alignItems: "center", justifyContent: "center" },
  logo: { fontSize: 56, marginBottom: 8 },
  title: { fontSize: 40, fontWeight: "700", color: colors.ink },
  tagline: { fontSize: 15, color: colors.muted, marginTop: 8, textAlign: "center" },
  cta: { gap: 12 },
  hint: { color: colors.muted, fontSize: 13, textAlign: "center", marginTop: 4 },
  erreur: { color: colors.scoreZero, fontSize: 13, textAlign: "center" },
});
