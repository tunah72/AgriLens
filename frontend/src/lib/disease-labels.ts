const DISEASE_LABELS: Record<string, string> = {
  Healthy: "Healthy",
  BrownSpot: "Brown Spot",
  Hispa: "Rice Hispa",
  LeafBlast: "Leaf Blast",
  LeafMiner: "Leaf Miner",
  PowderyMildew: "Powdery Mildew",
  Rust: "Rust",
  AlgalLeafSpot: "Algal Leaf Spot",
};

export function getDiseaseDisplayName(label: string) {
  return DISEASE_LABELS[label] ?? "Unknown Disease";
}
