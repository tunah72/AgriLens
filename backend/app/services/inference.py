"""
ONNX Runtime inference service for the FastAPI backend.
"""

import io
import json
from pathlib import Path
import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image


DISEASE_COLOR_MAP: dict[str, tuple[int, int, int]] = {
    "LeafBlast": (239, 68, 68),       # Red
    "BrownSpot": (217, 119, 6),       # Amber / Brown
    "Hispa": (99, 102, 241),          # Indigo
    "BacterialBlight": (234, 179, 8), # Yellow
    "Rust": (249, 115, 22),           # Orange
    "PowderyMildew": (244, 63, 94),   # Rose
    "Cercospora": (236, 72, 153),     # Pink
    "AlgalLeafSpot": (6, 182, 212),   # Cyan
    "LeafMiner": (168, 85, 247),      # Purple
    "Healthy": (16, 185, 129),        # Emerald / Green
}
DEFAULT_DETECTION_COLOR = (245, 158, 11)


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
                    Path("artifacts/yolo26_seg_joint/yolo26n_seg_joint_int8.onnx"),
                    Path("artifacts/yolo26_seg_joint/yolo26n_seg_joint.onnx"),
                    Path(__file__).resolve().parents[3] / "artifacts/yolo26_seg_joint/yolo26n_seg_joint_int8.onnx",
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

    def _decode_detections_and_masks(
        self,
        outputs: list[np.ndarray],
        orig_w: int,
        orig_h: int,
        active_class_names: list[str],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.5,
    ) -> tuple[list[dict], list[np.ndarray | None]]:
        """Extract bounding boxes and instance segmentation masks from ONNX outputs."""
        if not outputs:
            return [], []

        out0 = np.asarray(outputs[0])
        if out0.ndim == 3 and out0.shape[0] == 1:
            out0 = out0[0]
            if out0.shape[0] < out0.shape[1]:
                out0 = out0.T

        if out0.ndim != 2 or out0.shape[1] not in (38, 6):
            return [], []

        protos = None
        if len(outputs) > 1 and outputs[1] is not None:
            p = np.asarray(outputs[1])
            if p.ndim == 4 and p.shape[0] == 1:
                protos = p[0]
            elif p.ndim == 3:
                protos = p

        rows = []
        boxes_nms = []
        scores_nms = []

        scale_x = orig_w / float(self.input_size)
        scale_y = orig_h / float(self.input_size)

        for row in out0:
            conf = float(row[4])
            cls_id = int(row[5])
            if conf < conf_threshold:
                continue
            if cls_id < 0 or cls_id >= len(active_class_names):
                continue
            cls_name = active_class_names[cls_id]
            if cls_name == "Healthy":
                continue

            x1_inp, y1_inp, x2_inp, y2_inp = row[:4]
            x1 = max(0.0, float(x1_inp * scale_x))
            y1 = max(0.0, float(y1_inp * scale_y))
            x2 = min(float(orig_w), float(x2_inp * scale_x))
            y2 = min(float(orig_h), float(y2_inp * scale_y))
            w = max(0.0, x2 - x1)
            h = max(0.0, y2 - y1)
            if w <= 1 or h <= 1:
                continue

            rows.append((row, cls_name, cls_id, conf, [x1, y1, x2, y2]))
            boxes_nms.append([int(x1), int(y1), int(w), int(h)])
            scores_nms.append(conf)

        if not rows:
            return [], []

        nms_indices = cv2.dnn.NMSBoxes(
            boxes_nms,
            scores_nms,
            score_threshold=conf_threshold,
            nms_threshold=iou_threshold,
        )
        if len(nms_indices) == 0:
            return [], []
        if isinstance(nms_indices, np.ndarray):
            nms_indices = nms_indices.flatten().tolist()

        detections = []
        masks: list[np.ndarray | None] = []

        for idx in nms_indices:
            row, cls_name, cls_id, conf, orig_box = rows[idx]
            x1, y1, x2, y2 = orig_box
            mask_orig = None
            polygons: list[list[list[int]]] = []
            area_pct = 0.0

            if protos is not None and len(row) >= 38:
                coeffs = row[6:38]
                c, mh, mw = protos.shape
                raw_mask = np.matmul(coeffs, protos.reshape(c, -1)).reshape(mh, mw)
                sig_mask = 1.0 / (1.0 + np.exp(-raw_mask))

                proto_scale = mw / float(self.input_size)
                bx1 = max(0, int(row[0] * proto_scale))
                by1 = max(0, int(row[1] * proto_scale))
                bx2 = min(mw, int(np.ceil(row[2] * proto_scale)))
                by2 = min(mh, int(np.ceil(row[3] * proto_scale)))

                cropped = np.zeros_like(sig_mask)
                cropped[by1:by2, bx1:bx2] = sig_mask[by1:by2, bx1:bx2]
                bin_proto = (cropped > 0.5).astype(np.uint8)

                mask_orig = cv2.resize(bin_proto, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
                nonzero = np.count_nonzero(mask_orig)
                area_pct = round(float(nonzero) / float(orig_w * orig_h) * 100.0, 2)

                contours, _ = cv2.findContours(mask_orig, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    if len(cnt) >= 3:
                        eps = max(1.0, 0.005 * cv2.arcLength(cnt, True))
                        approx = cv2.approxPolyDP(cnt, eps, True)
                        pts = approx.squeeze(1).tolist()
                        if isinstance(pts, list) and len(pts) >= 3:
                            polygons.append(pts)
            else:
                area_pct = round(((x2 - x1) * (y2 - y1) / float(orig_w * orig_h)) * 100.0, 2)

            detections.append({
                "label": cls_name,
                "confidence": round(conf, 4),
                "box": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
                "class_id": cls_id,
                "polygon": polygons[0] if polygons else None,
                "polygons": polygons,
                "area_pct": float(area_pct),
            })
            masks.append(mask_orig)

        return detections, masks

    def annotate_image(
        self,
        orig_image: Image.Image,
        detections: list[dict],
        masks: list[np.ndarray | None],
    ) -> bytes | None:
        """Render bounding boxes, transparent mask overlay, and badges onto leaf image."""
        if not detections:
            return None

        img_np = np.array(orig_image.convert("RGB"))
        overlay = img_np.copy()

        for det, mask in zip(detections, masks):
            label = det["label"]
            color = DISEASE_COLOR_MAP.get(label, DEFAULT_DETECTION_COLOR)

            # 1. Overlay segmentation mask if available
            if mask is not None and np.count_nonzero(mask) > 0:
                m_bool = mask > 0
                overlay[m_bool] = (np.array(color) * 0.45 + overlay[m_bool] * 0.55).astype(np.uint8)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(overlay, contours, -1, color, 2)

            # 2. Draw bounding box
            x1, y1, x2, y2 = [int(v) for v in det["box"]]
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)

            # 3. Draw badge
            conf_pct = int(det["confidence"] * 100)
            text = f"{label} {conf_pct}%"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            bx1 = x1
            by1 = max(0, y1 - th - 6)
            bx2 = x1 + tw + 6
            by2 = max(th + 6, y1)
            cv2.rectangle(overlay, (bx1, by1), (bx2, by2), color, -1)
            cv2.putText(
                overlay,
                text,
                (bx1 + 3, by2 - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        bgr = cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR)
        success, buf = cv2.imencode(".jpg", bgr, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        if not success:
            return None
        return buf.tobytes()

    def predict_segmentation(
        self,
        image_bytes: bytes,
        filename: str | None = None,
        crop: str | None = None,
        top_k: int = 5,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.5,
    ) -> tuple[list[tuple[str, float]], list[dict], bytes | None]:
        """
        Run inference, decode instance segmentation masks and bounding boxes,
        and generate an annotated visual overlay image.

        Returns:
            (top_k_predictions, detections, annotated_image_bytes)
        """
        try:
            orig_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:
            raise InvalidImageError(f"Failed to decode image: {exc}") from exc

        orig_w, orig_h = orig_image.size
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
            coffee_outputs = self.coffee_session.run(None, {self.coffee_input_name: tensor})
            coffee_scores = self._class_scores_from_output_for_classes(coffee_outputs[0], len(self.coffee_class_names))
            max_coffee_conf = float(coffee_scores.max())

            rice_outputs = self.rice_session.run(None, {self.rice_input_name: tensor})
            rice_scores = self._class_scores_from_output_for_classes(rice_outputs[0], len(self.rice_class_names))
            max_rice_conf = float(rice_scores.max())

            if inferred_crop == "coffee":
                use_coffee = True
            elif inferred_crop == "rice":
                use_coffee = False
            else:
                use_coffee = max_coffee_conf > max_rice_conf

            if use_coffee:
                scores = coffee_scores
                active_class_names = self.coffee_class_names
                selected_outputs = coffee_outputs
            else:
                scores = rice_scores
                active_class_names = self.rice_class_names
                selected_outputs = rice_outputs
        else:
            selected_outputs = self.session.run(None, {self.input_name: tensor})
            scores = self._class_scores_from_output(selected_outputs[0])
            active_class_names = self.class_names

        k = min(top_k, len(active_class_names))
        indexes = np.argsort(scores)[::-1][:k]
        top_k_preds = [(active_class_names[idx], float(scores[idx])) for idx in indexes]

        detections, masks = self._decode_detections_and_masks(
            outputs=selected_outputs,
            orig_w=orig_w,
            orig_h=orig_h,
            active_class_names=active_class_names,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold,
        )

        annotated_bytes = self.annotate_image(orig_image, detections, masks) if detections else None
        return top_k_preds, detections, annotated_bytes

    def predict(
        self,
        image_bytes: bytes,
        filename: str | None = None,
        crop: str | None = None,
        top_k: int = 5,
    ) -> list[tuple[str, float]]:
        """Run inference and return top-k (label, confidence) pairs."""
        top_k_preds, _, _ = self.predict_segmentation(
            image_bytes=image_bytes,
            filename=filename,
            crop=crop,
            top_k=top_k,
        )
        return top_k_preds
