"""
ONNX Runtime inference service for the FastAPI backend.
"""

import io
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image


class InvalidImageError(ValueError):
    """Exception raised when the uploaded file cannot be parsed as an image."""

    pass


class InferenceService:
    """ONNX Runtime inference service."""

    def __init__(self, model_path: str, class_names: list[str], input_size: int = 640):
        model_file = Path(model_path)
        if not class_names:
            raise ValueError("class_names must not be empty")

        self.input_size = input_size
        parent_dir = model_file.parent

        # Locate Rice and Coffee models
        rice_path = parent_dir / "yolo26_rice_quantized.onnx"
        coffee_path = parent_dir / "yolo26_coffee_quantized.onnx"

        if rice_path.exists() and coffee_path.exists():
            self.rice_session = ort.InferenceSession(str(rice_path), providers=["CPUExecutionProvider"])
            self.rice_input_name = self.rice_session.get_inputs()[0].name
            self.rice_class_names = ["BrownSpot", "Healthy", "Hispa", "LeafBlast"]

            self.coffee_session = ort.InferenceSession(str(coffee_path), providers=["CPUExecutionProvider"])
            self.coffee_input_name = self.coffee_session.get_inputs()[0].name
            self.coffee_class_names = ["AlgalLeafSpot", "LeafMiner", "PowderyMildew", "Rust"]

            self.has_both = True
        else:
            if not model_file.exists():
                candidates = [
                    Path(".") / model_path.lstrip("/"),
                    Path(__file__).resolve().parents[3] / model_path.lstrip("/"),
                    Path("artifacts/yolo26_seg_joint/yolo26n_seg_joint.onnx"),
                    Path(__file__).resolve().parents[3] / "artifacts/yolo26_seg_joint/yolo26n_seg_joint.onnx",
                    Path("models/yolo26_quantized.onnx"),
                ]
                for cand in candidates:
                    if cand.exists():
                        model_file = cand
                        break
                else:
                    raise FileNotFoundError(f"ONNX model not found: {model_path}")
            self.session = ort.InferenceSession(str(model_file), providers=["CPUExecutionProvider"])
            self.input_name = self.session.get_inputs()[0].name
            self.class_names = class_names
            self.has_both = False

    @staticmethod
    def load_class_names(path: str) -> list[str]:
        p = Path(path)
        if not p.exists():
            candidates = [
                Path(".") / path.lstrip("/"),
                Path(__file__).resolve().parents[3] / path.lstrip("/"),
                Path("models/class_names.json"),
                Path(__file__).resolve().parents[3] / "models/class_names.json",
            ]
            for cand in candidates:
                if cand.exists():
                    p = cand
                    break
            else:
                raise FileNotFoundError(f"Class names file not found: {path}")
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [str(item) for item in data]
        if isinstance(data, dict):
            names = data.get("names", data)
            if isinstance(names, dict):
                return [
                    str(names[key])
                    for key in sorted(names, key=lambda value: int(value) if str(value).isdigit() else value)
                ]
            if isinstance(names, list):
                return [str(item) for item in names]
        raise ValueError(f"Unsupported class names format: {path}")

    def preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Convert image bytes to a normalized NCHW float32 tensor."""
        try:
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image = image.resize((self.input_size, self.input_size))
            array = np.asarray(image, dtype=np.float32) / 255.0
            array = np.transpose(array, (2, 0, 1))
            return np.expand_dims(array, axis=0).astype(np.float32)
        except Exception as exc:
            raise InvalidImageError(f"Failed to decode or preprocess image: {exc}") from exc

    @staticmethod
    def _softmax(scores: np.ndarray) -> np.ndarray:
        scores = scores.astype(np.float32)
        scores = scores - np.max(scores)
        exp_scores = np.exp(scores)
        return exp_scores / np.sum(exp_scores)

    def _class_scores_from_output_for_classes(self, output: np.ndarray, class_count: int) -> np.ndarray:
        output = np.asarray(output)
        if output.ndim == 3 and output.shape[0] == 1:
            output = output[0]
            if output.shape[0] < output.shape[1]:
                output = output.T

            # Check if this is an End-to-End YOLO model (e.g. [300, 38] with box, conf, class_id, mask_coeffs)
            # Standard YOLO output shape for End-to-End is (300, 6 + num_masks) = (300, 38)
            if output.shape[1] in (38, 6):
                scores = np.zeros(class_count, dtype=np.float32)
                for row in output:
                    conf = float(row[4])
                    class_id = int(row[5])
                    if 0 <= class_id < class_count:
                        scores[class_id] = max(scores[class_id], conf)
                if class_count == 8 and len(self.class_names) == 8 and self.class_names[7] == "Healthy":
                    max_disease_conf = float(scores[:7].max())
                    scores[7] = max(0.0, 1.0 - max_disease_conf)
                return scores
            if output.shape[1] >= 4 + class_count:
                return output[:, 4 : 4 + class_count].max(axis=0)
        if output.ndim == 2:
            if output.shape[0] == 1:
                output = output[0]
            elif output.shape[1] == class_count:
                return output.max(axis=0)
        if output.ndim == 1 and output.shape[0] >= class_count:
            return output[:class_count]
        raise ValueError(f"Unsupported ONNX output shape: {output.shape}")

    def _class_scores_from_output(self, output: np.ndarray) -> np.ndarray:
        class_count = len(self.rice_class_names) if self.has_both else len(self.class_names)
        return self._class_scores_from_output_for_classes(output, class_count)

    def predict(
        self,
        image_bytes: bytes,
        filename: str | None = None,
        crop: str | None = None,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """Run inference and return top-k (label, confidence) pairs."""
        tensor = self.preprocess(image_bytes)

        # Determine crop
        inferred_crop = None
        if crop:
            inferred_crop = crop.lower()
        elif filename:
            name_lower = filename.lower()
            if any(k in name_lower for k in ("coffee", "caphe", "ca_phe", "ca-phe")):
                inferred_crop = "coffee"
            elif any(k in name_lower for k in ("rice", "lua", "rice-leaf", "lalua")):
                inferred_crop = "rice"

        if self.has_both:
            # 1. Run Coffee model inference to get scores and max confidence
            coffee_outputs = self.coffee_session.run(None, {self.coffee_input_name: tensor})
            coffee_scores = self._class_scores_from_output_for_classes(coffee_outputs[0], len(self.coffee_class_names))
            max_coffee_conf = float(coffee_scores.max())

            # 2. Run Rice model inference to get scores and max confidence
            rice_outputs = self.rice_session.run(None, {self.rice_input_name: tensor})
            rice_scores = self._class_scores_from_output_for_classes(rice_outputs[0], len(self.rice_class_names))
            max_rice_conf = float(rice_scores.max())

            # Determine routing
            if inferred_crop == "coffee":
                use_coffee = True
            elif inferred_crop == "rice":
                use_coffee = False
            else:
                # Fallback to max confidence comparison
                use_coffee = max_coffee_conf > max_rice_conf

            if use_coffee:
                probabilities = coffee_scores
                k = min(top_k, len(self.coffee_class_names))
                indexes = np.argsort(probabilities)[::-1][:k]
                return [(self.coffee_class_names[index], float(probabilities[index])) for index in indexes]
            else:
                probabilities = rice_scores
                k = min(top_k, len(self.rice_class_names))
                indexes = np.argsort(probabilities)[::-1][:k]
                return [(self.rice_class_names[index], float(probabilities[index])) for index in indexes]
        else:
            outputs = self.session.run(None, {self.input_name: tensor})
            scores = self._class_scores_from_output(outputs[0])
            probabilities = scores
            k = min(top_k, len(self.class_names))
            indexes = np.argsort(probabilities)[::-1][:k]
            return [(self.class_names[index], float(probabilities[index])) for index in indexes]
