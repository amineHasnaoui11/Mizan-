import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { colors } from "./src/theme";
import { AccueilScreen } from "./src/screens/AccueilScreen";
import { DevoirsScreen } from "./src/screens/DevoirsScreen";
import { NouveauDevoirScreen } from "./src/screens/NouveauDevoirScreen";
import { ScanScreen } from "./src/screens/ScanScreen";
import { ResultatScreen } from "./src/screens/ResultatScreen";
import { ExerciceScreen } from "./src/screens/ExerciceScreen";
import type { RootStackParamList } from "./src/screens/types";

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="dark" />
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: colors.paper },
          headerTintColor: colors.ink,
          headerTitleStyle: { fontWeight: "600" },
          contentStyle: { backgroundColor: colors.paper },
        }}
      >
        <Stack.Screen name="Accueil" component={AccueilScreen} options={{ headerShown: false }} />
        <Stack.Screen name="Devoirs" component={DevoirsScreen} options={{ title: "Mes devoirs" }} />
        <Stack.Screen name="NouveauDevoir" component={NouveauDevoirScreen} options={{ title: "Nouveau devoir" }} />
        <Stack.Screen name="Scan" component={ScanScreen} options={{ title: "Corriger une copie" }} />
        <Stack.Screen name="Exercice" component={ExerciceScreen} options={{ title: "Corriger un exercice" }} />
        <Stack.Screen name="Resultat" component={ResultatScreen} options={{ title: "Résultat" }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
