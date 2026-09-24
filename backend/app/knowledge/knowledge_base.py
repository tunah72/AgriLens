"""Expert Knowledge Base - rule-based plant disease recommendations."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from typing import Any

DISEASES_DB_PATH = os.path.join(os.path.dirname(__file__), "diseases.json")
REQUIRED_LABELS = {
    "Healthy",
    "BrownSpot",
    "Hispa",
    "LeafBlast",
    "LeafMiner",
    "PowderyMildew",
    "Rust",
    "AlgalLeafSpot",
}
REQUIRED_FIELDS = {
    "label",
    "name_vi",
    "name_en",
    "crop",
    "description",
    "symptoms",
    "causes",
    "treatments",
    "prevention",
    "severity",
    "sources",
}
ALLOWED_SEVERITIES = {"none", "low", "medium", "high"}
ADVISORY_TEXT = (
    "Recommendations are for reference based on the input image. Verify field conditions and consult local "
    "plant protection specialists before applying chemical treatments or large-scale interventions."
)
ADVISORY_TEXT_VI = (
    "Khuyến nghị chỉ mang tính chất tham khảo dựa trên ảnh phân tích. Cần đối chiếu thực tế đồng ruộng và "
    "tham vấn chuyên gia bảo vệ thực vật địa phương trước khi tiến hành xử lý hóa chất hoặc can thiệp trên diện rộng."
)


class KnowledgeBase:
    """Lookup table for disease descriptions and farmer-facing recommendations."""

    def __init__(self, db_path: str = DISEASES_DB_PATH):
        self.db_path = db_path
        self._diseases = self._load_diseases(db_path)

    def list_diseases(self) -> list[dict[str, Any]]:
        """Return compact metadata for all diseases in stable label order."""
        return [
            {
                "label": disease["label"],
                "crop": disease["crop"],
                "name_vi": disease["name_vi"],
                "name_en": disease["name_en"],
                "severity": disease["severity"],
            }
            for _, disease in sorted(self._diseases.items())
        ]

    def get_disease_info(self, disease_label: str) -> dict[str, Any] | None:
        """Return full disease information for a model label."""
        disease = self._diseases.get(disease_label)
        if disease is None:
            return None
        return deepcopy(disease)

    def format_recommendation(self, disease_label: str, confidence: float) -> dict[str, Any]:
        """Format disease data for the prediction API response."""
        self._validate_confidence(confidence)
        disease = self.get_disease_info(disease_label)
        confidence_note = self._confidence_note(confidence)
        confidence_note_vi = self._confidence_note_vi(confidence)
        if disease is None:
            return {
                "label": disease_label,
                "crop": None,
                "name_vi": "Chưa có dữ liệu khuyến nghị",
                "name_en": disease_label,
                "description": "Predicted label is not present in the expert knowledge base.",
                "symptoms": [],
                "causes": [],
                "treatments": [
                    "Retake clearer photos of both the upper and lower leaf surfaces.",
                    "Verify field symptoms and consult local plant protection specialists.",
                ],
                "prevention": [
                    "Monitor neighboring plants before deciding on intervention.",
                    "Avoid applying chemical treatments when disease diagnosis is uncertain.",
                ],
                "severity": "medium",
                "sources": [],
                "confidence": confidence,
                "confidence_note": confidence_note,
                "confidence_note_vi": confidence_note_vi,
                "advisory": ADVISORY_TEXT,
                "advisory_vi": ADVISORY_TEXT_VI,
            }
        disease["confidence"] = confidence
        disease["confidence_note"] = confidence_note
        disease["confidence_note_vi"] = confidence_note_vi
        disease["advisory"] = ADVISORY_TEXT
        disease["advisory_vi"] = ADVISORY_TEXT_VI
        return disease

    @staticmethod
    def _validate_confidence(confidence: float) -> None:
        if not isinstance(confidence, int | float) or not 0 <= confidence <= 1:
            raise ValueError("Prediction confidence must be a number between 0 and 1.")

    @staticmethod
    def _confidence_note(confidence: float) -> str:
        if confidence < 0.6:
            return (
                f"Low confidence ({confidence:.1%}). Please capture from another angle or inspect the plant directly."
            )
        return f"Diagnosis confidence: {confidence:.1%}."

    @staticmethod
    def _confidence_note_vi(confidence: float) -> str:
        if confidence < 0.6:
            return (
                f"Độ tin cậy chưa cao ({confidence:.1%}). Khuyến nghị: Chụp lại ảnh lá rõ nét hơn hoặc đối chiếu trực tiếp trên đồng ruộng."
            )
        return f"Độ tin cậy chẩn đoán: {confidence:.1%}."
    @classmethod
    def _load_diseases(cls, db_path: str) -> dict[str, dict[str, Any]]:
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Knowledge base file not found: {db_path}")

        with open(db_path, encoding="utf-8") as file:
            payload = json.load(file)

        diseases = payload.get("diseases")
        if not isinstance(diseases, dict):
            raise ValueError("Knowledge base must contain a 'diseases' object.")

        cls._validate_diseases(diseases)
        return deepcopy(diseases)

    @classmethod
    def _validate_diseases(cls, diseases: dict[str, Any]) -> None:
        labels = set(diseases)
        missing_labels = REQUIRED_LABELS - labels
        extra_labels = labels - REQUIRED_LABELS
        if missing_labels:
            raise ValueError(f"Knowledge base missing labels: {sorted(missing_labels)}")
        if extra_labels:
            raise ValueError(f"Knowledge base has unsupported labels: {sorted(extra_labels)}")

        for label, disease in diseases.items():
            if not isinstance(disease, dict):
                raise ValueError(f"Disease record for {label} must be an object.")
            cls._validate_disease_record(label, disease)

    @classmethod
    def _validate_disease_record(cls, label: str, disease: dict[str, Any]) -> None:
        missing_fields = REQUIRED_FIELDS - set(disease)
        if missing_fields:
            raise ValueError(f"Disease record {label} missing fields: {sorted(missing_fields)}")
        if disease["label"] != label:
            raise ValueError(f"Disease record {label} has mismatched label field: {disease['label']}")
        if disease["severity"] not in ALLOWED_SEVERITIES:
            raise ValueError(f"Disease record {label} has invalid severity: {disease['severity']}")

        for field in REQUIRED_FIELDS:
            value = disease[field]
            if cls._is_empty(value):
                raise ValueError(f"Disease record {label} has empty field: {field}")
            if cls._contains_todo(value):
                raise ValueError(f"Disease record {label} still contains placeholder text in field: {field}")

        for field in ("symptoms", "causes", "treatments", "prevention"):
            if not isinstance(disease[field], list) or not all(isinstance(item, str) for item in disease[field]):
                raise ValueError(f"Disease record {label} field {field} must be a list of strings.")

        if not isinstance(disease["sources"], list) or not disease["sources"]:
            raise ValueError(f"Disease record {label} field sources must be a non-empty list.")
        for source in disease["sources"]:
            if not isinstance(source, dict) or not isinstance(source.get("title"), str) or not source.get("title"):
                raise ValueError(f"Disease record {label} has an invalid source entry.")
            url = source.get("url")
            if not isinstance(url, str) or not url.startswith(("http://", "https://")):
                raise ValueError(f"Disease record {label} has an invalid source URL.")

    @staticmethod
    def _is_empty(value: Any) -> bool:
        return value is None or value == "" or value == []

    @classmethod
    def _contains_todo(cls, value: Any) -> bool:
        if isinstance(value, str):
            return "TODO" in value.upper()
        if isinstance(value, list):
            return any(cls._contains_todo(item) for item in value)
        if isinstance(value, dict):
            return any(cls._contains_todo(item) for item in value.values())
        return False
