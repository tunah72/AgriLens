export const DISEASE_LABELS_VI: Record<string, string> = {
  Healthy: "Khỏe mạnh",
  BrownSpot: "Bệnh đốm nâu hại lúa",
  Hispa: "Bọ gai hại lúa",
  LeafBlast: "Bệnh đạo ôn lá lúa",
  LeafMiner: "Sâu vẽ bùa hại cà phê",
  PowderyMildew: "Bệnh phấn trắng hại cà phê",
  Rust: "Bệnh rỉ sắt hại cà phê",
  AlgalLeafSpot: "Bệnh đốm rong hại cà phê",
  InvalidLeaf: "Không phải lá cây hợp lệ",
};

export const DISEASE_LABELS_EN: Record<string, string> = {
  Healthy: "Healthy",
  BrownSpot: "Brown Spot",
  Hispa: "Rice Hispa",
  LeafBlast: "Leaf Blast",
  LeafMiner: "Leaf Miner",
  PowderyMildew: "Powdery Mildew",
  Rust: "Rust",
  AlgalLeafSpot: "Algal Leaf Spot",
  InvalidLeaf: "Invalid Leaf Specimen",
};

export function getDiseaseDisplayName(label: string, lang: "vi" | "en" = "vi"): string {
  if (lang === "en") {
    return DISEASE_LABELS_EN[label] ?? "Unknown Disease";
  }
  return DISEASE_LABELS_VI[label] ?? "Bệnh chưa xác định";
}
