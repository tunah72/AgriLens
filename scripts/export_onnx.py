"""Export trained PyTorch / YOLO segmentation checkpoints to ONNX and perform INT8 quantization."""

import argparse
import os
import shutil
import sys
import time
from pathlib import Path


def parse_args():
    """Parse CLI arguments for model export and quantization."""
    parser = argparse.ArgumentParser(
        description="Export and quantize plant disease segmentation models for ONNX serving."
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        required=True,
        help="Path to trained PyTorch / Ultralytics checkpoint (e.g. best.pt)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Target output ONNX path (default: <checkpoint_stem>.onnx)",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=1024,
        help="Input image resolution for export (default: 1024)",
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=17,
        help="ONNX opset version (default: 17)",
    )
    parser.add_argument(
        "--quantize",
        action="store_true",
        help="Perform INT8 dynamic quantization for CPU serving",
    )
    return parser.parse_args()


def export_yolo_to_onnx(checkpoint: Path, imgsz: int, opset: int) -> Path:
    """Export Ultralytics YOLO checkpoint to ONNX."""
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: 'ultralytics' is required for YOLO checkpoint export.")
        print("Install with: pip install ultralytics")
        sys.exit(1)

    print(f"Loading checkpoint from: {checkpoint}")
    model = YOLO(str(checkpoint))

    print(f"Exporting to ONNX (imgsz={imgsz}, opset={opset}, simplify=True)...")
    start_time = time.time()
    exported_file = model.export(
        format="onnx",
        imgsz=imgsz,
        opset=opset,
        simplify=True,
    )
    elapsed = time.time() - start_time
    print(f"ONNX export completed in {elapsed:.2f}s -> {exported_file}")
    return Path(exported_file)


def quantize_onnx_model(onnx_path: Path, output_path: Path | None = None) -> Path:
    """Perform INT8 dynamic quantization on an ONNX model."""
    try:
        import onnx  # noqa: F401
        from onnxruntime.quantization import QuantType, quantize_dynamic
    except ImportError:
        print("Error: 'onnx' and 'onnxruntime' are required for INT8 quantization.")
        print("Install with: pip install onnx onnxruntime")
        sys.exit(1)

    if output_path is None:
        output_path = onnx_path.parent / f"{onnx_path.stem}_int8.onnx"

    print(f"\nStarting INT8 dynamic quantization: {onnx_path} -> {output_path}...")
    start_time = time.time()
    quantize_dynamic(
        model_input=str(onnx_path),
        model_output=str(output_path),
        weight_type=QuantType.QUInt8,
    )
    elapsed = time.time() - start_time

    orig_size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    quant_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    reduction = (1 - quant_size_mb / orig_size_mb) * 100

    print(f"Quantization completed in {elapsed:.2f}s:")
    print(f"  - FP32 model size: {orig_size_mb:.2f} MB")
    print(f"  - INT8 model size: {quant_size_mb:.2f} MB")
    print(f"  - Size reduction:  {reduction:.1f}%")

    return output_path


def main():
    """Main export and quantization runner."""
    args = parse_args()

    if not args.checkpoint.exists():
        print(f"Error: Checkpoint file not found at: {args.checkpoint}")
        sys.exit(1)

    exported_onnx = export_yolo_to_onnx(
        checkpoint=args.checkpoint,
        imgsz=args.imgsz,
        opset=args.opset,
    )

    final_onnx = args.output or exported_onnx
    if args.output and exported_onnx.resolve() != args.output.resolve():
        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(exported_onnx, args.output)
        final_onnx = args.output
        print(f"Saved ONNX model to: {final_onnx}")

    if args.quantize:
        quantized_output = (
            final_onnx.parent / f"{final_onnx.stem}_int8.onnx"
            if not args.output
            else args.output.parent / f"{args.output.stem}_int8.onnx"
        )
        quantize_onnx_model(final_onnx, quantized_output)

    print("\nAll export tasks completed successfully.")


if __name__ == "__main__":
    main()
