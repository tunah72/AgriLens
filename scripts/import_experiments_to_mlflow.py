"""
Import existing Kaggle experiment artifacts into local MLflow Tracking Server.

Reads:
- run_manifest.json -> hyperparameters, architecture, dataset, domain
- summary.csv -> final test metrics (mask mAP, box mAP, Dice, mIoU, latency)
- training_curves.csv -> epoch-by-epoch loss & mAP curves
- Plot images (*.png) & contracts (*.json) -> artifacts
"""

import argparse
import csv
import os
import json
import logging
import re
from pathlib import Path
import mlflow

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mlflow_importer")


def clean_metric_name(name: str) -> str:
    """Sanitize metric names to conform to MLflow naming constraints."""
    # MLflow allows alphanumerics, underscores, dashes, periods, spaces, colons, slashes
    cleaned = re.sub(r"[^\w\.\-\s/:]", "_", name)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def import_experiment_run(artifact_path: Path, experiment_id: str) -> str | None:
    """Import a single experiment folder into MLflow."""
    folder_name = artifact_path.name
    logger.info(f"Processing experiment artifact: {folder_name}")

    manifest_path = artifact_path / "run_manifest.json"
    summary_path = artifact_path / "summary.csv"
    curves_path = artifact_path / "training_curves.csv"

    run_name = folder_name.replace("_", "-")

    with mlflow.start_run(experiment_id=experiment_id, run_name=run_name) as run:
        # 1. Log Manifest & Parameters
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                mlflow.log_param("domain", manifest.get("domain", folder_name))
                mlflow.log_param("architecture", manifest.get("model", {}).get("weights_init", folder_name))
                mlflow.log_param("dataset_version", manifest.get("dataset", {}).get("version", "unknown"))

                train_args = manifest.get("train_args", {})
                for k, v in train_args.items():
                    # Only log simple scalar parameters
                    if isinstance(v, (int, float, str, bool)):
                        mlflow.log_param(f"arg_{k}", v)
            except Exception as e:
                logger.warning(f"Failed to parse run_manifest.json in {folder_name}: {e}")
        else:
            mlflow.log_param("domain", folder_name)

        # 2. Log Final Summary Metrics
        if summary_path.exists():
            try:
                with open(summary_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        for k, v in row.items():
                            try:
                                mlflow.log_metric(f"final_{clean_metric_name(k)}", float(v))
                            except (ValueError, TypeError):
                                pass
            except Exception as e:
                logger.warning(f"Failed to read summary.csv in {folder_name}: {e}")

        # 3. Log Epoch-by-Epoch Training Curves
        if curves_path.exists():
            try:
                with open(curves_path, mode="r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    epoch_count = 0
                    for row in reader:
                        epoch = int(float(row.get("epoch", epoch_count + 1)))
                        metrics = {}
                        for k, v in row.items():
                            if k in ("epoch", "time"):
                                continue
                            try:
                                metrics[clean_metric_name(k)] = float(v)
                            except (ValueError, TypeError):
                                pass
                        if metrics:
                            mlflow.log_metrics(metrics, step=epoch)
                            epoch_count += 1
                logger.info(f"  -> Logged {epoch_count} training curve epochs for {run_name}")
            except Exception as e:
                logger.warning(f"Failed to log training curves for {folder_name}: {e}")

        # 4. Log Visual Plots & Model Contracts as Artifacts
        artifact_files = [
            "results.png",
            "confusion_matrix_normalized.png",
            "MaskPR_curve.png",
            "BoxPR_curve.png",
            "serving_contract.json",
            "serving_contract_int8.json",
            "quantization_benchmark.json",
            "domain_breakdown_metrics.json",
            "ultralytics_args.yaml",
        ]
        for fname in artifact_files:
            fpath = artifact_path / fname
            if fpath.exists():
                try:
                    mlflow.log_artifact(str(fpath))
                except Exception as e:
                    logger.warning(f"Failed to log artifact {fname}: {e}")

        logger.info(f"  -> Successfully created Run ID: {run.info.run_id}")
        return run.info.run_id


def main():
    parser = argparse.ArgumentParser(description="Import Kaggle training artifacts into MLflow")
    parser.add_argument(
        "--tracking-uri",
        default=os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"),
        help="MLflow tracking URI (default: http://localhost:5001 or $MLFLOW_TRACKING_URI)",
    )
    parser.add_argument(
        "--experiment-name",
        default="Coffee-Rice-Leaf-Disease-Benchmarks",
        help="Target MLflow experiment name",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="artifacts",
        help="Path to directory containing experiment folders",
    )
    args = parser.parse_args()

    mlflow.set_tracking_uri(args.tracking_uri)
    logger.info(f"Connecting to MLflow at {args.tracking_uri}")

    client = mlflow.MlflowClient()
    exp = client.get_experiment_by_name(args.experiment_name)
    if exp is None:
        exp_id = client.create_experiment(args.experiment_name)
        logger.info(f"Created new Experiment: {args.experiment_name} (ID: {exp_id})")
    else:
        exp_id = exp.experiment_id
        logger.info(f"Using existing Experiment: {args.experiment_name} (ID: {exp_id})")

    artifacts_root = Path(args.artifacts_dir)
    if not artifacts_root.exists():
        logger.error(f"Artifacts directory not found: {artifacts_root}")
        return

    # Scan for subdirectories
    subdirs = [p for p in artifacts_root.iterdir() if p.is_dir() and not p.name.startswith(".")]
    if not subdirs:
        logger.warning(f"No experiment folders found inside {artifacts_root}")
        return

    logger.info(f"Found {len(subdirs)} experiment folders: {[p.name for p in subdirs]}")
    for subdir in sorted(subdirs):
        import_experiment_run(subdir, exp_id)

    logger.info(f"Import completed successfully! Open your browser at {args.tracking_uri} to view.")


if __name__ == "__main__":
    main()
