"""Production-grade ONNX INT8 Dynamic Quantization for YOLO26-seg Joint Multi-Domain Model.

Optimized for CPU real-time inference in AgriLens:
- Preserves prototype mask branch (/model.23/proto/...) in FP32 to avoid runtime
  dynamic activation quantization overhead on 256x256 feature maps and retain
  high mask fidelity (mIoU / Dice).
- Preserves post-processing, Sigmoid/SiLU activations, and TopK/NMS nodes in FP32.
- Quantizes backbone and feature pyramid network Conv layers to INT8.
"""

from __future__ import annotations

import argparse
import logging
import os
import shutil
import time
from pathlib import Path

import numpy as np
import onnx
import onnxruntime as ort
from onnxruntime.quantization import QuantType, quantize_dynamic

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def find_proto_conv_nodes(model: onnx.ModelProto) -> list[str]:
    """Find all Conv nodes inside the prototype mask generator branch."""
    proto_nodes: list[str] = []
    for node in model.graph.node:
        if "proto" in node.name and node.op_type == "Conv":
            proto_nodes.append(node.name)
    return proto_nodes


def quantize_yolo26_seg(
    input_model_path: str | Path,
    output_model_path: str | Path,
    weight_type: QuantType = QuantType.QUInt8,
    preserve_proto_masks: bool = True,
    reduce_range: bool = False,
) -> Path:
    """Quantize YOLO26-seg FP32 ONNX model to INT8 with architecture-aware exclusions."""
    input_path = Path(input_model_path)
    output_path = Path(output_model_path)

    if not input_path.exists():
        raise FileNotFoundError(f"Input ONNX model not found: {input_path}")

    logger.info("Loading ONNX model: %s", input_path)
    model = onnx.load(str(input_path))

    nodes_to_exclude: list[str] = []
    if preserve_proto_masks:
        proto_convs = find_proto_conv_nodes(model)
        nodes_to_exclude.extend(proto_convs)
        logger.info(
            "Preserving %d prototype mask Conv nodes in FP32: %s",
            len(proto_convs),
            proto_convs,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Starting INT8 dynamic quantization -> %s", output_path)
    start_time = time.perf_counter()

    quantize_dynamic(
        model_input=str(input_path),
        model_output=str(output_path),
        weight_type=weight_type,
        nodes_to_exclude=nodes_to_exclude if nodes_to_exclude else None,
        reduce_range=reduce_range,
    )
    elapsed = time.perf_counter() - start_time

    # Validate output model
    logger.info("Validating quantized ONNX model structure...")
    quant_model = onnx.load(str(output_path))
    onnx.checker.check_model(quant_model)

    # Sanity check with ONNX Runtime session
    sess = ort.InferenceSession(str(output_path), providers=["CPUExecutionProvider"])
    dummy_input = np.zeros((1, 3, 1024, 1024), dtype=np.float32)
    outputs = sess.run(None, {sess.get_inputs()[0].name: dummy_input})

    orig_size_bytes = os.path.getsize(input_path)
    quant_size_bytes = os.path.getsize(output_path)
    compression_ratio = orig_size_bytes / quant_size_bytes
    reduction_pct = (1.0 - quant_size_bytes / orig_size_bytes) * 100.0

    logger.info("Quantization completed in %.2fs", elapsed)
    logger.info("  Original size:    %.2f MB (%d bytes)", orig_size_bytes / 1024 / 1024, orig_size_bytes)
    logger.info("  Quantized size:   %.2f MB (%d bytes)", quant_size_bytes / 1024 / 1024, quant_size_bytes)
    logger.info("  Compression:      %.2fx (%.1f%% reduction)", compression_ratio, reduction_pct)
    logger.info("  Output 0 shape:   %s", outputs[0].shape)
    logger.info("  Output 1 shape:   %s", outputs[1].shape)

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Quantize YOLO26-seg FP32 model to INT8.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("artifacts/yolo26_seg_joint/yolo26n_seg_joint.onnx"),
        help="Path to FP32 ONNX model",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/yolo26_seg_joint/yolo26n_seg_joint_int8.onnx"),
        help="Path to output INT8 ONNX model",
    )
    parser.add_argument(
        "--sync-models-dir",
        type=Path,
        default=Path("models/yolo26_quantized.onnx"),
        help="Path to copy quantized model for backend serving (default: models/yolo26_quantized.onnx)",
    )
    parser.add_argument(
        "--weight-type",
        choices=["QUInt8", "QInt8"],
        default="QUInt8",
        help="Quantization weight type (QUInt8 or QInt8)",
    )
    parser.add_argument(
        "--no-preserve-proto",
        action="store_true",
        help="Disable prototype mask Conv exclusion",
    )
    args = parser.parse_args()

    weight_type = QuantType.QUInt8 if args.weight_type == "QUInt8" else QuantType.QInt8

    quantized_path = quantize_yolo26_seg(
        input_model_path=args.input,
        output_model_path=args.output,
        weight_type=weight_type,
        preserve_proto_masks=not args.no_preserve_proto,
    )

    if args.sync_models_dir:
        args.sync_models_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(quantized_path, args.sync_models_dir)
        logger.info("Synced quantized model to serving location: %s", args.sync_models_dir)


if __name__ == "__main__":
    main()
