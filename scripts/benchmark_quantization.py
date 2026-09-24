"""Comprehensive CPU Benchmark & Trade-off Analysis: FP32 vs INT8 YOLO26-seg.

Measures:
1. Model Footprint (Disk MB, in-memory footprint, compression ratio)
2. CPU Latency & Throughput (warmup, 100 runs: Mean, P50, P90, P95, P99, FPS)
3. Peak Memory Consumption (RSS memory increase via psutil)
4. Output Fidelity (Prototype Mask Cosine Similarity, MSE, Instance Dice score, mIoU, Top-1 class agreement)
"""

from __future__ import annotations

import argparse
import glob
import json
import logging
import multiprocessing as mp
import os
import platform
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import psutil
from PIL import Image

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50.0, 50.0)))


def compute_dice_and_iou(m1: np.ndarray, m2: np.ndarray) -> tuple[float, float]:
    inter = np.logical_and(m1, m2).sum()
    union = np.logical_or(m1, m2).sum()
    dice = float((2.0 * inter) / (m1.sum() + m2.sum() + 1e-7))
    iou = float(inter / (union + 1e-7))
    return dice, iou


def _run_latency_and_memory_worker(
    model_path: str,
    num_runs: int,
    warmup_runs: int,
    image_shape: tuple[int, int, int, int],
    return_dict: dict,
) -> None:
    """Isolated subprocess to measure session memory and pure CPU inference latency."""
    try:
        proc = psutil.Process()
        rss_start = proc.memory_info().rss

        # Load session
        t_load_0 = time.perf_counter()
        sess = ort.InferenceSession(
            model_path,
            providers=["CPUExecutionProvider"],
            sess_options=ort.SessionOptions(),
        )
        t_load_ms = (time.perf_counter() - t_load_0) * 1000.0
        rss_after_load = proc.memory_info().rss
        input_name = sess.get_inputs()[0].name

        dummy_input = np.random.randn(*image_shape).astype(np.float32)

        # Warmup
        for _ in range(warmup_runs):
            sess.run(None, {input_name: dummy_input})

        # Benchmark runs
        latencies: list[float] = []
        rss_peaks: list[int] = []

        for _ in range(num_runs):
            t0 = time.perf_counter()
            sess.run(None, {input_name: dummy_input})
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)
            rss_peaks.append(proc.memory_info().rss)

        rss_max = max(rss_peaks) if rss_peaks else rss_after_load

        return_dict["load_time_ms"] = float(t_load_ms)
        return_dict["model_memory_mb"] = float((rss_after_load - rss_start) / (1024 * 1024))
        return_dict["peak_memory_mb"] = float(rss_max / (1024 * 1024))
        return_dict["latencies"] = [float(x) for x in latencies]
    except Exception as exc:
        import traceback

        traceback.print_exc()
        return_dict["error"] = str(exc)


def benchmark_latency_and_memory(
    model_path: str | Path,
    num_runs: int = 100,
    warmup_runs: int = 10,
    image_shape: tuple[int, int, int, int] = (1, 3, 1024, 1024),
) -> dict:
    """Run benchmark in separate process for clean memory isolation."""
    manager = mp.Manager()
    return_dict = manager.dict()

    p = mp.Process(
        target=_run_latency_and_memory_worker,
        args=(str(model_path), num_runs, warmup_runs, image_shape, return_dict),
    )
    p.start()
    p.join()

    latencies = np.array(return_dict["latencies"])
    mean_ms = float(np.mean(latencies))
    std_ms = float(np.std(latencies))
    p50_ms = float(np.percentile(latencies, 50))
    p90_ms = float(np.percentile(latencies, 90))
    p95_ms = float(np.percentile(latencies, 95))
    p99_ms = float(np.percentile(latencies, 99))
    min_ms = float(np.min(latencies))
    max_ms = float(np.max(latencies))
    fps = float(1000.0 / mean_ms) if mean_ms > 0 else 0.0

    return {
        "num_runs": num_runs,
        "warmup_runs": warmup_runs,
        "load_time_ms": return_dict["load_time_ms"],
        "model_memory_mb": return_dict["model_memory_mb"],
        "peak_memory_mb": return_dict["peak_memory_mb"],
        "latency_mean_ms": round(mean_ms, 2),
        "latency_std_ms": round(std_ms, 2),
        "latency_p50_ms": round(p50_ms, 2),
        "latency_p90_ms": round(p90_ms, 2),
        "latency_p95_ms": round(p95_ms, 2),
        "latency_p99_ms": round(p99_ms, 2),
        "latency_min_ms": round(min_ms, 2),
        "latency_max_ms": round(max_ms, 2),
        "throughput_fps": round(fps, 2),
    }


def benchmark_threaded_latency(
    model_path: str | Path,
    thread_configs: list[int] = (1, 2, 4),
    num_runs: int = 30,
    warmup_runs: int = 5,
    image_shape: tuple[int, int, int, int] = (1, 3, 1024, 1024),
) -> dict[str, dict]:
    """Benchmark latency across standard container vCPU thread limits."""
    dummy = np.random.randn(*image_shape).astype(np.float32)
    results = {}

    for threads in thread_configs:
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = threads
        opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        sess = ort.InferenceSession(str(model_path), opts, providers=["CPUExecutionProvider"])
        inp_name = sess.get_inputs()[0].name

        for _ in range(warmup_runs):
            sess.run(None, {inp_name: dummy})

        times = []
        for _ in range(num_runs):
            t0 = time.perf_counter()
            sess.run(None, {inp_name: dummy})
            times.append((time.perf_counter() - t0) * 1000.0)

        results[f"{threads}_vcpu"] = {
            "threads": threads,
            "latency_mean_ms": round(float(np.mean(times)), 2),
            "latency_p50_ms": round(float(np.percentile(times, 50)), 2),
            "latency_p95_ms": round(float(np.percentile(times, 95)), 2),
            "throughput_fps": round(float(1000.0 / np.mean(times)), 2),
        }
    return results


def evaluate_fidelity(
    fp32_path: str | Path,
    int8_path: str | Path,
    qa_images_glob: str = "artifacts/**/label_qa/*.jpg",
) -> dict:
    """Evaluate output fidelity and mask overlap on real validation/QA images."""
    image_paths = sorted(glob.glob(qa_images_glob, recursive=True))
    if not image_paths:
        logger.warning("No QA images found matching %s", qa_images_glob)
        return {}

    sess_fp32 = ort.InferenceSession(str(fp32_path), providers=["CPUExecutionProvider"])
    sess_int8 = ort.InferenceSession(str(int8_path), providers=["CPUExecutionProvider"])

    proto_cossims: list[float] = []
    proto_mses: list[float] = []
    mask_dices: list[float] = []
    mask_ious: list[float] = []
    conf_diffs: list[float] = []
    class_matches: list[bool] = []

    for img_p in image_paths:
        img = Image.open(img_p).convert("RGB").resize((1024, 1024))
        x = np.array(img, dtype=np.float32) / 255.0
        x = np.transpose(x, (2, 0, 1))[None, ...]

        o0_fp, o1_fp = sess_fp32.run(None, {"images": x})
        o0_int, o1_int = sess_int8.run(None, {"images": x})

        # Prototype mask cosine similarity and MSE
        sim = float(np.dot(o1_fp.flatten(), o1_int.flatten()) / (np.linalg.norm(o1_fp) * np.linalg.norm(o1_int) + 1e-9))
        proto_cossims.append(sim)
        proto_mses.append(float(np.mean((o1_fp - o1_int) ** 2)))

        # Top-1 detection comparison
        if o0_fp.shape[1] > 0 and o0_int.shape[1] > 0:
            top_f = np.argmax(o0_fp[0, :, 4])
            top_q = np.argmax(o0_int[0, :, 4])
            conf_diffs.append(float(abs(o0_fp[0, top_f, 4] - o0_int[0, top_q, 4])))
            class_matches.append(int(o0_fp[0, top_f, 5]) == int(o0_int[0, top_q, 5]))

        # Mask decoding and Dice/IoU calculation on top proposals
        top_indices = np.argsort(o0_fp[0, :, 4])[::-1][:3]
        for idx in top_indices:
            coeffs_fp = o0_fp[0, idx, 6:38]
            coeffs_int = o0_int[0, idx, 6:38]
            protos_fp = o1_fp[0].reshape(32, -1)
            protos_int = o1_int[0].reshape(32, -1)

            m_fp = sigmoid(coeffs_fp @ protos_fp).reshape(256, 256) > 0.5
            m_int = sigmoid(coeffs_int @ protos_int).reshape(256, 256) > 0.5

            if m_fp.sum() > 0 or m_int.sum() > 0:
                dice, iou = compute_dice_and_iou(m_fp, m_int)
                mask_dices.append(dice)
                mask_ious.append(iou)

    return {
        "num_evaluated_images": len(image_paths),
        "proto_cosine_similarity_mean": round(float(np.mean(proto_cossims)), 5),
        "proto_cosine_similarity_std": round(float(np.std(proto_cossims)), 5),
        "proto_mse": round(float(np.mean(proto_mses)), 6),
        "instance_mask_dice": round(float(np.mean(mask_dices)), 4),
        "instance_mask_miou": round(float(np.mean(mask_ious)), 4),
        "top1_confidence_mae": round(float(np.mean(conf_diffs)), 4),
        "top1_class_agreement_rate": round(float(np.mean(class_matches) * 100.0), 2),
    }


def run_full_benchmark(
    fp32_path: Path,
    int8_path: Path,
    num_runs: int = 100,
    warmup_runs: int = 10,
    output_json: Path | None = None,
) -> dict:
    """Run full benchmark comparing FP32 and INT8 models."""
    logger.info("==================================================")
    logger.info("   YOLO26-seg Quantization Trade-off Benchmark")
    logger.info("==================================================")

    fp32_size_bytes = os.path.getsize(fp32_path)
    int8_size_bytes = os.path.getsize(int8_path)
    compression_ratio = fp32_size_bytes / int8_size_bytes
    reduction_pct = (1.0 - int8_size_bytes / fp32_size_bytes) * 100.0

    model_sizes = {
        "fp32_size_mb": round(fp32_size_bytes / (1024 * 1024), 2),
        "int8_size_mb": round(int8_size_bytes / (1024 * 1024), 2),
        "compression_ratio": round(compression_ratio, 2),
        "size_reduction_pct": round(reduction_pct, 2),
    }

    logger.info("1. Measuring CPU Latency & RAM for FP32 model (%d runs)...", num_runs)
    fp32_bench = benchmark_latency_and_memory(fp32_path, num_runs=num_runs, warmup_runs=warmup_runs)

    logger.info("2. Measuring CPU Latency & RAM for INT8 model (%d runs)...", num_runs)
    int8_bench = benchmark_latency_and_memory(int8_path, num_runs=num_runs, warmup_runs=warmup_runs)
    logger.info("3. Profiling container vCPU limits (1 vCPU, 2 vCPUs, 4 vCPUs)...")
    fp32_threads = benchmark_threaded_latency(fp32_path, thread_configs=[1, 2, 4], num_runs=25)
    int8_threads = benchmark_threaded_latency(int8_path, thread_configs=[1, 2, 4], num_runs=25)

    logger.info("4. Evaluating Fidelity & Overlap on real QA images...")
    fidelity = evaluate_fidelity(fp32_path, int8_path)

    speedup_ratio = round(fp32_bench["latency_mean_ms"] / int8_bench["latency_mean_ms"], 2)
    latency_reduction_pct = round((1.0 - int8_bench["latency_mean_ms"] / fp32_bench["latency_mean_ms"]) * 100.0, 2)

    result = {
        "system_info": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "python_version": platform.python_version(),
            "onnxruntime_version": ort.__version__,
        },
        "model_footprint": model_sizes,
        "latency_and_throughput": {
            "fp32": fp32_bench,
            "int8": int8_bench,
            "speedup_ratio": speedup_ratio,
            "latency_reduction_pct": latency_reduction_pct,
            "container_vcpu_scaling": {
                "fp32": fp32_threads,
                "int8": int8_threads,
            },
        },
        "fidelity_tradeoff": fidelity,
    }
    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        logger.info("Benchmark results saved to: %s", output_json)

    # Print summary table
    print("\n" + "=" * 76)
    print("                YOLO26-seg FP32 vs INT8 QUANTIZATION BENCHMARK")
    print("=" * 76)
    print(f"{'Metric':<32} | {'FP32 Baseline':<18} | {'INT8 Quantized':<18}")
    print("-" * 76)
    fp32_sz = f"{model_sizes['fp32_size_mb']:<14.2f} MB"
    int8_sz = f"{model_sizes['int8_size_mb']:<14.2f} MB ({reduction_pct:.1f}% reduction)"
    print(f"{'Model Size (Disk)':<32} | {fp32_sz} | {int8_sz}")
    fp32_pr = f"{fp32_bench['peak_memory_mb']:<14.2f} MB"
    int8_pr = f"{int8_bench['peak_memory_mb']:<14.2f} MB"
    print(f"{'Peak RAM Consumption':<32} | {fp32_pr} | {int8_pr}")
    fp32_lm = f"{fp32_bench['model_memory_mb']:<14.2f} MB"
    int8_lm = f"{int8_bench['model_memory_mb']:<14.2f} MB"
    print(f"{'Model Load Memory':<32} | {fp32_lm} | {int8_lm}")
    fp32_lat = f"{fp32_bench['latency_mean_ms']:<14.2f} ms"
    int8_lat = f"{int8_bench['latency_mean_ms']:<14.2f} ms ({speedup_ratio:.2f}x faster)"
    print(f"{'CPU Mean Latency':<32} | {fp32_lat} | {int8_lat}")
    fp32_p50 = f"{fp32_bench['latency_p50_ms']:<14.2f} ms"
    int8_p50 = f"{int8_bench['latency_p50_ms']:<14.2f} ms"
    print(f"{'CPU P50 (Median) Latency':<32} | {fp32_p50} | {int8_p50}")
    fp32_p90 = f"{fp32_bench['latency_p90_ms']:<14.2f} ms"
    int8_p90 = f"{int8_bench['latency_p90_ms']:<14.2f} ms"
    print(f"{'CPU P90 Latency':<32} | {fp32_p90} | {int8_p90}")
    fp32_p95 = f"{fp32_bench['latency_p95_ms']:<14.2f} ms"
    int8_p95 = f"{int8_bench['latency_p95_ms']:<14.2f} ms"
    print(f"{'CPU P95 Latency':<32} | {fp32_p95} | {int8_p95}")
    fp32_p99 = f"{fp32_bench['latency_p99_ms']:<14.2f} ms"
    int8_p99 = f"{int8_bench['latency_p99_ms']:<14.2f} ms"
    print(f"{'CPU P99 Latency':<32} | {fp32_p99} | {int8_p99}")
    fp32_fps = f"{fp32_bench['throughput_fps']:<14.2f} FPS"
    int8_fps = f"{int8_bench['throughput_fps']:<14.2f} FPS"
    print(f"{'Throughput (Unconstrained)':<32} | {fp32_fps}| {int8_fps}")
    print("-" * 76)
    t1_ratio = (
        fp32_threads["1_vcpu"]["latency_mean_ms"] / int8_threads["1_vcpu"]["latency_mean_ms"]
    )
    t1_f = f"{fp32_threads['1_vcpu']['latency_mean_ms']:<14.2f} ms"
    t1_i = f"{int8_threads['1_vcpu']['latency_mean_ms']:<14.2f} ms ({t1_ratio:.2f}x faster)"
    print(f"{'Container 1 vCPU Latency (Mean)':<32} | {t1_f} | {t1_i}")
    t1_p95_f = f"{fp32_threads['1_vcpu']['latency_p95_ms']:<14.2f} ms"
    t1_p95_i = f"{int8_threads['1_vcpu']['latency_p95_ms']:<14.2f} ms"
    print(f"{'Container 1 vCPU P95 Latency':<32} | {t1_p95_f} | {t1_p95_i}")
    t2_ratio = (
        fp32_threads["2_vcpu"]["latency_mean_ms"] / int8_threads["2_vcpu"]["latency_mean_ms"]
    )
    t2_f = f"{fp32_threads['2_vcpu']['latency_mean_ms']:<14.2f} ms"
    t2_i = f"{int8_threads['2_vcpu']['latency_mean_ms']:<14.2f} ms ({t2_ratio:.2f}x faster)"
    print(f"{'Container 2 vCPU Latency (Mean)':<32} | {t2_f} | {t2_i}")
    t2_p95_f = f"{fp32_threads['2_vcpu']['latency_p95_ms']:<14.2f} ms"
    t2_p95_i = f"{int8_threads['2_vcpu']['latency_p95_ms']:<14.2f} ms"
    print(f"{'Container 2 vCPU P95 Latency':<32} | {t2_p95_f} | {t2_p95_i}")
    t4_ratio = (
        fp32_threads["4_vcpu"]["latency_mean_ms"] / int8_threads["4_vcpu"]["latency_mean_ms"]
    )
    t4_f = f"{fp32_threads['4_vcpu']['latency_mean_ms']:<14.2f} ms"
    t4_i = f"{int8_threads['4_vcpu']['latency_mean_ms']:<14.2f} ms ({t4_ratio:.2f}x faster)"
    print(f"{'Container 4 vCPU Latency (Mean)':<32} | {t4_f} | {t4_i}")
    print("-" * 76)
    proto_sim = f"{fidelity['proto_cosine_similarity_mean']:<18.5f}"
    print(f"{'Prototype Mask Cosine Sim':<32} | {'1.00000 (Exact)':<18} | {proto_sim}")
    print(f"{'Prototype Mask MSE':<32} | {'0.000000':<18} | {fidelity['proto_mse']:<18.6f}")
    print(f"{'Instance Mask Dice Score':<32} | {'1.0000 (Exact)':<18} | {fidelity['instance_mask_dice']:<18.4f}")
    print(f"{'Instance Mask mIoU':<32} | {'1.0000 (Exact)':<18} | {fidelity['instance_mask_miou']:<18.4f}")
    print(f"{'Top-1 Class Agreement':<32} | {'100.0%':<18} | {fidelity['top1_class_agreement_rate']:<17.1f}%")
    print("=" * 76 + "\n")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark FP32 vs INT8 ONNX models.")
    parser.add_argument(
        "--fp32",
        type=Path,
        default=Path("artifacts/yolo26_seg_joint/yolo26n_seg_joint.onnx"),
        help="Path to FP32 model",
    )
    parser.add_argument(
        "--int8",
        type=Path,
        default=Path("artifacts/yolo26_seg_joint/yolo26n_seg_joint_int8.onnx"),
        help="Path to INT8 model",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=100,
        help="Number of benchmark iterations (default: 100)",
    )
    parser.add_argument(
        "--warmup",
        type=int,
        default=10,
        help="Number of warmup iterations (default: 10)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/yolo26_seg_joint/quantization_benchmark.json"),
        help="Path to save benchmark JSON output",
    )
    args = parser.parse_args()

    run_full_benchmark(
        fp32_path=args.fp32,
        int8_path=args.int8,
        num_runs=args.runs,
        warmup_runs=args.warmup,
        output_json=args.output,
    )


if __name__ == "__main__":
    main()
