import { useCallback, useState } from "react";
import { View, Text, StyleSheet, SafeAreaView, ScrollView, TouchableOpacity } from "react-native";
import { useFocusEffect } from "@react-navigation/native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { colors } from "../theme";
import { Button, Card } from "../components/UI";
import { listerDevoirs, type DevoirResume } from "../api";
import type { RootStackParamList } from "./types";

type Props = NativeStackScreenProps<RootStackParamList, "Devoirs">;

export function DevoirsScreen({ navigation }: Props) {
  const [devoirs, setDevoirs] = useState<DevoirResume[]>([]);
  const [erreur, setErreur] = useState<string | null>(null);
  const [charge, setCharge] = useState(false);

  useFocusEffect(
    useCallback(() => {
      setErreur(null);
      listerDevoirs()
        .then((d) => {
          setDevoirs(d);
          setCharge(true);
        })
        .catch((e) => {
          setErreur(e instanceof Error ? e.message : String(e));
          setCharge(true);
        });
    }, []),
  );

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.content}>
        <Button title="➕ Nouveau devoir" onPress={() => navigation.navigate("NouveauDevoir")} />

        {erreur && <Text style={styles.erreur}>{erreur}</Text>}

        {charge && devoirs.length === 0 && !erreur && (
          <Card style={{ marginTop: 16 }}>
            <Text style={styles.empty}>Aucun devoir pour l'instant.</Text>
            <Text style={styles.emptySub}>Crée-en un en photographiant devoir + barème + corrigé.</Text>
          </Card>
        )}

        <View style={{ marginTop: 16, gap: 10 }}>
          {devoirs.map((d) => (
            <Card key={d.devoir_id}>
              <Text style={styles.dTitre}>{d.matiere || d.devoir_id}</Text>
              <Text style={styles.dSub}>
                {d.niveau ? `${d.niveau} · ` : ""}{d.nb_questions} questions · {d.note_max_devoir} pts
              </Text>
              <View style={styles.actions}>
                <TouchableOpacity onPress={() => navigation.navigate("Scan", { devoirId: d.devoir_id })}>
                  <Text style={styles.dAction}>📷 Corriger une copie</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={() => navigation.navigate("Analyse", { devoirId: d.devoir_id, matiere: d.matiere || d.devoir_id })}>
                  <Text style={styles.dAction}>📊 Analyse de la classe</Text>
                </TouchableOpacity>
              </View>
            </Card>
          ))}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  content: { padding: 16, paddingBottom: 40 },
  erreur: { color: colors.scoreZero, marginTop: 14, fontSize: 14 },
  empty: { color: colors.ink, fontWeight: "600", fontSize: 15 },
  emptySub: { color: colors.muted, fontSize: 13, marginTop: 4 },
  dTitre: { fontSize: 16, fontWeight: "700", color: colors.ink },
  dSub: { fontSize: 13, color: colors.muted, marginTop: 2 },
  actions: { flexDirection: "row", justifyContent: "space-between", marginTop: 12, flexWrap: "wrap", gap: 8 },
  dAction: { fontSize: 13, color: colors.accent, fontWeight: "600" },
});
