import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { colors } from "./src/theme";
import { LangProvider, useLang } from "./src/i18n";
import { AccueilScreen } from "./src/screens/AccueilScreen";
import { DevoirsScreen } from "./src/screens/DevoirsScreen";
import { NouveauDevoirScreen } from "./src/screens/NouveauDevoirScreen";
import { ScanScreen } from "./src/screens/ScanScreen";
import { ResultatScreen } from "./src/screens/ResultatScreen";
import { ExerciceScreen } from "./src/screens/ExerciceScreen";
import { AnalyseScreen } from "./src/screens/AnalyseScreen";
import type { RootStackParamList } from "./src/screens/types";

const Stack = createNativeStackNavigator<RootStackParamList>();

function Nav() {
  const { t } = useLang();
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
        <Stack.Screen name="Devoirs" component={DevoirsScreen} options={{ title: t("nav_devoirs") }} />
        <Stack.Screen name="NouveauDevoir" component={NouveauDevoirScreen} options={{ title: t("nav_nouveau") }} />
        <Stack.Screen name="Scan" component={ScanScreen} options={{ title: t("nav_scan") }} />
        <Stack.Screen name="Exercice" component={ExerciceScreen} options={{ title: t("nav_exercice") }} />
        <Stack.Screen name="Analyse" component={AnalyseScreen} options={{ title: t("nav_analyse") }} />
        <Stack.Screen name="Resultat" component={ResultatScreen} options={{ title: t("nav_resultat") }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

export default function App() {
  return (
    <LangProvider>
      <Nav />
    </LangProvider>
  );
}
