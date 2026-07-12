import { ReactNode } from "react";
import {
  Text,
  TouchableOpacity,
  View,
  StyleSheet,
  ActivityIndicator,
  StyleProp,
  ViewStyle,
} from "react-native";
import { colors, radius } from "../theme";

export function Button({
  title,
  onPress,
  variant = "accent",
  disabled,
  loading,
}: {
  title: string;
  onPress: () => void;
  variant?: "accent" | "ink" | "outline";
  disabled?: boolean;
  loading?: boolean;
}) {
  const bg = variant === "outline" ? colors.surface : variant === "ink" ? colors.ink : colors.accent;
  const fg = variant === "outline" ? colors.ink : colors.white;
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.85}
      style={[
        styles.btn,
        { backgroundColor: bg, opacity: disabled || loading ? 0.5 : 1 },
        variant === "outline" && { borderWidth: 1, borderColor: colors.line },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={fg} />
      ) : (
        <Text style={[styles.btnText, { color: fg }]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
}

export function Card({ children, style }: { children: ReactNode; style?: StyleProp<ViewStyle> }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Badge({ text, color }: { text: string; color: string }) {
  return (
    <View style={[styles.badge, { backgroundColor: color }]}>
      <Text style={styles.badgeText}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  btn: {
    height: 52,
    borderRadius: radius.lg,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 20,
  },
  btnText: { fontSize: 16, fontWeight: "600" },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    borderWidth: 1,
    borderColor: colors.line,
    padding: 16,
  },
  badge: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 3, alignSelf: "flex-start" },
  badgeText: { color: colors.white, fontSize: 12, fontWeight: "600" },
});
