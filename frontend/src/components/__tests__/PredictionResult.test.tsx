import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { PredictionResponse } from "../../lib/api";
import PredictionResult from "../PredictionResult";
import { LanguageProvider } from "../../lib/i18n";

const mockPredictionWithDetections: PredictionResponse = {
  prediction: "LeafBlast",
  confidence: 0.92,
  top_k: [
    { label: "LeafBlast", confidence: 0.92 },
    { label: "Healthy", confidence: 0.08 },
  ],
  recommendation: {
    label: "LeafBlast",
    crop: "rice",
    name_vi: "Bệnh đạo ôn lá",
    name_en: "Rice Leaf Blast",
    severity: "high",
    symptoms: ["Oval lesion"],
    causes: ["Magnaporthe oryzae"],
    treatments: ["Fungicide"],
    prevention: ["Clean seed"],
  },
  annotated_image_url: "https://storage.local/annotated.jpg",
  detections: [
    {
      label: "LeafBlast",
      confidence: 0.92,
      box: [10, 200, 600, 600],
      class_id: 6,
      polygon: [[10, 200], [600, 200], [600, 600], [10, 600]],
      area_pct: 13.2,
    },
  ],
  latency_ms: 145,
};

describe("PredictionResult with segmentation detections", () => {
  it("renders diagnosis, confidence, and detected lesion summary", () => {
    render(
      <LanguageProvider>
        <PredictionResult prediction={mockPredictionWithDetections} />
      </LanguageProvider>
    );

    // Primary name
    expect(screen.getByText("Bệnh đạo ôn lá")).toBeInTheDocument();

    // Confidence appears in both main score and lesion badge
    expect(screen.getAllByText("92%")).toHaveLength(2);
    // Detected lesions section
    expect(screen.getByText("Số đốm bệnh")).toBeInTheDocument();
    expect(screen.getByText("1 vùng tổn thương")).toBeInTheDocument();
    expect(screen.getByText(/13.2%/)).toBeInTheDocument();
  });

  it("renders correctly when there are no detected lesion spots (e.g. Healthy leaf)", () => {
    const healthyPrediction: PredictionResponse = {
      prediction: "Healthy",
      confidence: 0.95,
      top_k: [{ label: "Healthy", confidence: 0.95 }],
      recommendation: {
        label: "Healthy",
        crop: "rice",
        name_vi: "Khỏe mạnh",
        name_en: "Healthy",
        severity: "none",
        symptoms: [],
        causes: [],
        treatments: [],
        prevention: [],
      },
      detections: [],
      latency_ms: 120,
    };

    render(
      <LanguageProvider>
        <PredictionResult prediction={healthyPrediction} />
      </LanguageProvider>
    );

    expect(screen.getByText("Khỏe mạnh")).toBeInTheDocument();
    expect(screen.queryByText("Số đốm bệnh")).not.toBeInTheDocument();
  });
});
