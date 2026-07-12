import { View, Text, StyleSheet, SafeAreaView } from "react-native";
import type { NativeStackScreenProps } from "@react-navigation/native-stack";
import { colors } from "../theme";
import { Button } from "../components/UI";
import type { RootStackParamList } from "./types";

type Props = NativeStackScreenProps<RootStackParamList, "Accueil">;

export function AccueilScreen({ navigation }: Props) {
  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <View style={styles.brand}>
          <Text style={styles.logo}>⚖️</Text>
          <Text style={styles.title}>Mizan</Text>
          <Text style={styles.tagline}>L'IA propose, le prof valide.</Text>
        </View>

        <View style={styles.cta}>
          <Button title="📷 Scanner une copie (noter)" onPress={() => navigation.navigate("Scan")} />
          <Button
            title="🧠 Corriger un exercice (libre)"
            variant="outline"
            onPress={() => navigation.navigate("Exercice")}
          />
          <Text style={styles.hint}>
            « Noter » = contre un devoir enregistré. « Libre » = corrigé direct, sans devoir.
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.paper },
  container: { flex: 1, justifyContent: "space-between", padding: 24, paddingBottom: 40 },
  brand: { flex: 1, alignItems: "center", justifyContent: "center" },
  logo: { fontSize: 56, marginBottom: 8 },
  title: { fontSize: 40, fontWeight: "700", color: colors.ink },
  tagline: { fontSize: 15, color: colors.muted, marginTop: 8 },
  cta: { gap: 12 },
  hint: { color: colors.muted, fontSize: 13, textAlign: "center", marginTop: 4 },
});
