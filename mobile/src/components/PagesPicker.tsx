import { View, Text, StyleSheet, Image, TouchableOpacity } from "react-native";
import * as ImagePicker from "expo-image-picker";
import { colors } from "../theme";
import type { ImagePage } from "../api";

/** Capture de pages (caméra ou galerie) avec miniatures — réutilisable. */
export function PagesPicker({
  label,
  hint,
  pages,
  onChange,
}: {
  label: string;
  hint?: string;
  pages: ImagePage[];
  onChange: (pages: ImagePage[]) => void;
}) {
  function ajouter(a: ImagePicker.ImagePickerAsset) {
    onChange([
      ...pages,
      { uri: a.uri, name: a.fileName ?? `page_${pages.length + 1}.jpg`, type: a.mimeType ?? "image/jpeg" },
    ]);
  }

  async function photo() {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) return;
    const res = await ImagePicker.launchCameraAsync({ quality: 0.7 });
    if (!res.canceled && res.assets?.[0]) ajouter(res.assets[0]);
  }

  async function galerie() {
    const res = await ImagePicker.launchImageLibraryAsync({ quality: 0.7 });
    if (!res.canceled && res.assets?.[0]) ajouter(res.assets[0]);
  }

  return (
    <View style={styles.wrap}>
      <Text style={styles.label}>
        {label} {pages.length > 0 && <Text style={styles.count}>({pages.length})</Text>}
      </Text>
      {hint && <Text style={styles.hint}>{hint}</Text>}
      <View style={styles.thumbs}>
        {pages.map((p, i) => (
          <View key={i} style={styles.thumbWrap}>
            <Image source={{ uri: p.uri }} style={styles.thumb} />
            <TouchableOpacity style={styles.x} onPress={() => onChange(pages.filter((_, j) => j !== i))}>
              <Text style={styles.xText}>×</Text>
            </TouchableOpacity>
          </View>
        ))}
        <TouchableOpacity style={styles.addTile} onPress={photo}>
          <Text style={styles.addIcon}>📷</Text>
          <Text style={styles.addText}>Photo</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.addTile} onPress={galerie}>
          <Text style={styles.addIcon}>🖼️</Text>
          <Text style={styles.addText}>Galerie</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { marginBottom: 4 },
  label: { fontSize: 14, fontWeight: "600", color: colors.ink },
  count: { color: colors.accent },
  hint: { fontSize: 12, color: colors.muted, marginTop: 2, marginBottom: 6 },
  thumbs: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 6 },
  thumbWrap: { position: "relative" },
  thumb: { width: 68, height: 90, borderRadius: 10, backgroundColor: colors.line },
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
  addTile: {
    width: 68,
    height: 90,
    borderRadius: 10,
    borderWidth: 1.5,
    borderColor: colors.line,
    borderStyle: "dashed",
    alignItems: "center",
    justifyContent: "center",
  },
  addIcon: { fontSize: 20 },
  addText: { fontSize: 11, color: colors.muted, marginTop: 2 },
});
