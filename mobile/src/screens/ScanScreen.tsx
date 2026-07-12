import { useEffect, useState } from "react";
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
import {
  listerDevoirs,
  obtenirDevoir,
  transcrire,
  noter,
  type DevoirResume,
  type ImagePage,
} from "../api";
import type { RootStackParamList } from "./types";

type Props = NativeStackScreenProps<RootStackParamList, "Scan">;

export function ScanScreen({ navigation }: Props) {
  const [devoirs, setDevoirs] = useState<DevoirResume[]>([]);
  const [devoirId, setDevoirId] = useState<string>("");
  const [eleve, setEleve] = useState("");
  const [pages, setPages] = useState<ImagePage[]>([]);
  const [statut, setStatut] = useState<string | null>(null);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    listerDevoirs()
      .then((d) => {
        setDevoirs(d);
        if (d[0]) setDevoirId(d[0].devoir_id);
      })
      .catch((e) => setErreur(`Impossible de charger les devoirs : ${e.message}`));
  }, []);

  async function ajouterPage() {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) {
      setErreur("Autorisation caméra refusée.");
      return;
    }
    const res = await ImagePicker.launchCameraAsync({ quality: 0.7 });
    if (res.canceled || !res.assets?.length) return;
    const a = res.assets[0];
    setPages((prev) => [
      ...prev,
      { uri: a.uri, name: a.fileName ?? `page_${prev.length + 1}.jpg`, type: a.mimeType ?? "image/jpeg" },
    ]);
  }

  async function corriger() {
    setErreur(null);
    if (!devoirId || pages.length === 0) return;
    const copieId = eleve.trim() ? eleve.trim().replace(/\s+/g, "_").toLowerCase() : "eleve";
    try {
      setStatut("Lecture de la copie…");
      const ref = await obtenirDevoir(devoirId);
      const t = await transcrire(ref, copieId, pages);
      setStatut("Notation en cours…");
      const correction = await noter(ref, copieId, t.transcriptions);
      setStatut(null);
      navigation.navigate("Resultat", { correction, eleve: eleve.trim() || copieId });
    } catch (e) {
      setStatut(null);
      setErreur(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Card>
          <Text style={styles.label}>Devoir</Text>
          <View style={styles.chips}>
            {devoirs.length === 0 && (
              <Text style={styles.muted}>Aucun devoir. Crée-en un dans l'app web d'abord.</Text>
            )}
            {devoirs.map((d) => (
              <TouchableOpacity
                key={d.devoir_id}
                onPress={() => setDevoirId(d.devoir_id)}
                style={[styles.chip, devoirId === d.devoir_id && styles.chipActive]}
              >
                <Text style={[styles.chipText, devoirId === d.devoir_id && styles.chipTextActive]}>
                  {d.matiere || d.devoir_id} · {d.note_max_devoir} pts
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={[styles.label, { marginTop: 16 }]}>Élève</Text>
          <TextInput
            value={eleve}
            onChangeText={setEleve}
            placeholder="Ex : Aziz Abdelli"
            placeholderTextColor={colors.muted}
            style={styles.input}
          />
        </Card>

        <Card style={{ marginTop: 16 }}>
          <Text style={styles.label}>Pages de la copie ({pages.length})</Text>
          <View style={styles.thumbs}>
            {pages.map((p, i) => (
              <View key={i} style={styles.thumbWrap}>
                <Image source={{ uri: p.uri }} style={styles.thumb} />
                <TouchableOpacity
                  style={styles.thumbX}
                  onPress={() => setPages((prev) => prev.filter((_, j) => j !== i))}
                >
                  <Text style={styles.thumbXText}>×</Text>
                </TouchableOpacity>
              </View>
            ))}
          </View>
          <View style={{ marginTop: 12 }}>
            <Button title="📷 Ajouter une page" variant="outline" onPress={ajouterPage} />
          </View>
        </Card>

        {erreur && <Text style={styles.erreur}>{erreur}</Text>}
        {statut && <Text style={styles.statut}>{statut}</Text>}

        <View style={{ marginTop: 20 }}>
          <Button
            title="Corriger la copie"
            onPress={corriger}
            disabled={!devoirId || pages.length === 0 || statut !== null}
            loading={statut !== null}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  content: { padding: 16, paddingBottom: 40 },
  label: { fontSize: 13, fontWeight: "600", color: colors.mutedStrong, marginBottom: 8 },
  muted: { color: colors.muted, fontSize: 14 },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.line,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  chipActive: { backgroundColor: colors.ink, borderColor: colors.ink },
  chipText: { color: colors.mutedStrong, fontSize: 13, fontWeight: "500" },
  chipTextActive: { color: colors.paper },
  input: {
    borderWidth: 1,
    borderColor: colors.line,
    borderRadius: radius.md,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 15,
    color: colors.ink,
    backgroundColor: colors.surface,
  },
  thumbs: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  thumbWrap: { position: "relative" },
  thumb: { width: 74, height: 96, borderRadius: 10, backgroundColor: colors.line },
  thumbX: {
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
  thumbXText: { color: colors.white, fontSize: 15, lineHeight: 18, fontWeight: "700" },
  erreur: { color: colors.scoreZero, marginTop: 14, fontSize: 14 },
  statut: { color: colors.muted, marginTop: 14, fontSize: 14 },
});
