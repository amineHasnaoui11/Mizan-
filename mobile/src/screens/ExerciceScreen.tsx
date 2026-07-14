import { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  ScrollView,
  TextInput,
  Image,
  TouchableOpacity,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { colors, radius } from "../theme";
import { Button, Card } from "../components/UI";
import { useLang } from "../i18n";
import { assistant, type ImagePage } from "../api";
import type { RootStackParamList } from "./types";

type Props = NativeStackScreenProps<RootStackParamList, "Exercice">;

/** Mode assistant libre : scanner un exercice → corrigé direct (sans devoir). */
export function ExerciceScreen(_props: Props) {
  const { t, rtlText } = useLang();
  const [pages, setPages] = useState<ImagePage[]>([]);
  const [consigne, setConsigne] = useState("");
  const [texte, setTexte] = useState<string | null>(null);
  const [statut, setStatut] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  async function ajouterPage() {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) return setErreur("Autorisation caméra refusée.");
    const res = await ImagePicker.launchCameraAsync({ quality: 0.7 });
    if (res.canceled || !res.assets?.length) return;
    const a = res.assets[0];
    setPages((p) => [...p, { uri: a.uri, name: a.fileName ?? `page_${p.length + 1}.jpg`, type: a.mimeType ?? "image/jpeg" }]);
  }

  async function corriger() {
    setErreur(null);
    setTexte(null);
    setStatut(true);
    try {
      const r = await assistant(pages, consigne);
      setTexte(r.texte);
    } catch (e) {
      setErreur(e instanceof Error ? e.message : String(e));
    } finally {
      setStatut(false);
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={[styles.intro, rtlText]}>{t("ex_intro")}</Text>

        <Card>
          <Text style={[styles.label, rtlText]}>{t("consigne")}</Text>
          <TextInput
            value={consigne}
            onChangeText={setConsigne}
            placeholder="Ex : résous et explique, ou corrige la réponse de l'élève"
            placeholderTextColor={colors.muted}
            style={styles.input}
            multiline
          />
          <Text style={[styles.label, { marginTop: 14 }, rtlText]}>{t("copie_eleve")} ({pages.length})</Text>
          <View style={styles.thumbs}>
            {pages.map((p, i) => (
              <View key={i} style={styles.thumbWrap}>
                <Image source={{ uri: p.uri }} style={styles.thumb} />
                <TouchableOpacity style={styles.x} onPress={() => setPages((prev) => prev.filter((_, j) => j !== i))}>
                  <Text style={styles.xText}>×</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
          <View style={{ marginTop: 12 }}>
            <Button title={t("ajouter_page")} variant="outline" onPress={ajouterPage} />
          </View>
        </Card>

        {erreur && <Text style={styles.erreur}>{erreur}</Text>}

        <View style={{ marginTop: 16 }}>
          <Button
            title={t("obtenir_corrige")}
            onPress={corriger}
            disabled={pages.length === 0 || statut}
            loading={statut}
          />
        </View>

        {texte && (
          <Card style={{ marginTop: 16 }}>
            <Text style={[styles.corrigeTitre, rtlText]}>{t("corrige")}</Text>
            <Text style={[styles.corrige, rtlText]}>{texte}</Text>
          </Card>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  content: { padding: 16, paddingBottom: 40 },
  intro: { color: colors.muted, fontSize: 14, marginBottom: 14 },
  label: { fontSize: 13, fontWeight: "600", color: colors.mutedStrong, marginBottom: 8 },
  input: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    padding: 12,
    fontSize: 15,
    color: colors.ink,
    minHeight: 44,
    backgroundColor: colors.surface,
  },
  thumbs: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  thumbWrap: { position: "relative" },
  thumb: { width: 74, height: 96, borderRadius: 10, backgroundColor: colors.line },
  x: {
    position: "absolute",
    top: -6,
    right: -6,
    backgroundColor: colors.scoreZero,
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: "center",
    justifyContent: "center",
  },
  xText: { color: colors.white, fontSize: 15, fontWeight: "700" },
  erreur: { color: colors.scoreZero, marginTop: 14, fontSize: 14 },
  corrigeTitre: { fontSize: 16, fontWeight: "700", color: colors.ink, marginBottom: 8 },
  corrige: { fontSize: 15, color: colors.ink, lineHeight: 22 },
});
