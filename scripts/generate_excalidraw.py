"""Generate the two Excalidraw architecture diagrams used in Chapter 5."""

from __future__ import annotations

import argparse
import json
import zlib
from pathlib import Path

COLORS = {
    "title": "#1e40af",
    "subtitle": "#3b82f6",
    "body": "#64748b",
    "text": "#374151",
    "primary_fill": "#dbeafe",
    "primary_stroke": "#1e40af",
    "secondary_fill": "#eff6ff",
    "secondary_stroke": "#1e3a5f",
    "success_fill": "#a7f3d0",
    "success_stroke": "#047857",
    "start_fill": "#fed7aa",
    "start_stroke": "#c2410c",
    "ai_fill": "#ddd6fe",
    "ai_stroke": "#6d28d9",
    "decision_fill": "#fef3c7",
    "decision_stroke": "#b45309",
    "warning_fill": "#fee2e2",
    "warning_stroke": "#dc2626",
    "evidence_bg": "#1e293b",
    "evidence_text": "#22c55e",
    "white": "#ffffff",
}


def _seed(element_id: str, salt: str = "seed") -> int:
    return zlib.crc32(f"{salt}:{element_id}".encode()) & 0x7FFFFFFF


def _base(element_id: str, element_type: str, x: float, y: float, width: float, height: float) -> dict:
    return {
        "id": element_id,
        "type": element_type,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "angle": 0,
        "strokeColor": COLORS["text"],
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "roundness": None,
        "seed": _seed(element_id),
        "version": 1,
        "versionNonce": _seed(element_id, "nonce"),
        "isDeleted": False,
        "boundElements": None,
        "updated": 1,
        "link": None,
        "locked": False,
    }


def text(
    element_id: str,
    x: float,
    y: float,
    width: float,
    value: str,
    *,
    size: int = 18,
    color: str = COLORS["text"],
    align: str = "center",
) -> dict:
    lines = value.count("\n") + 1
    height = max(size * 1.25 * lines, size * 1.25)
    element = _base(element_id, "text", x, y, width, height)
    element.update(
        {
            "strokeColor": color,
            "text": value,
            "originalText": value,
            "fontSize": size,
            "fontFamily": 3,
            "textAlign": align,
            "verticalAlign": "middle",
            "containerId": None,
            "lineHeight": 1.25,
        }
    )
    return element


def rectangle(
    element_id: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str,
    dashed: bool = False,
    stroke_width: int = 2,
) -> dict:
    element = _base(element_id, "rectangle", x, y, width, height)
    element.update(
        {
            "strokeColor": stroke,
            "backgroundColor": fill,
            "strokeWidth": stroke_width,
            "strokeStyle": "dashed" if dashed else "solid",
            "roundness": {"type": 3},
        }
    )
    return element


def ellipse(
    element_id: str,
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str,
) -> dict:
    element = _base(element_id, "ellipse", x, y, width, height)
    element.update(
        {
            "strokeColor": stroke,
            "backgroundColor": fill,
            "strokeWidth": 2,
        }
    )
    return element


def arrow(
    element_id: str,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = COLORS["primary_stroke"],
    dashed: bool = False,
    width: int = 2,
) -> dict:
    x1, y1 = start
    x2, y2 = end
    dx, dy = x2 - x1, y2 - y1
    element = _base(element_id, "arrow", x1, y1, abs(dx), abs(dy))
    element.update(
        {
            "strokeColor": color,
            "strokeWidth": width,
            "strokeStyle": "dashed" if dashed else "solid",
            "roundness": {"type": 2},
            "points": [[0, 0], [dx, dy]],
            "lastCommittedPoint": [dx, dy],
            "startBinding": None,
            "endBinding": None,
            "startArrowhead": None,
            "endArrowhead": "arrow",
        }
    )
    return element


def box_with_text(
    element_id: str,
    x: float,
    y: float,
    width: float,
    height: float,
    value: str,
    *,
    fill: str,
    stroke: str,
    size: int = 18,
    text_color: str = COLORS["text"],
) -> list[dict]:
    lines = value.count("\n") + 1
    text_height = size * 1.25 * lines
    text_y = y + (height - text_height) / 2
    return [
        rectangle(element_id, x, y, width, height, fill=fill, stroke=stroke),
        text(f"{element_id}-text", x + 12, text_y, width - 24, value, size=size, color=text_color),
    ]


def evidence(
    element_id: str,
    x: float,
    y: float,
    width: float,
    value: str,
    *,
    size: int = 14,
) -> list[dict]:
    lines = value.count("\n") + 1
    height = 24 + lines * size * 1.25
    return [
        rectangle(
            element_id,
            x,
            y,
            width,
            height,
            fill=COLORS["evidence_bg"],
            stroke=COLORS["secondary_stroke"],
            stroke_width=1,
        ),
        text(
            f"{element_id}-text",
            x + 14,
            y + 12,
            width - 28,
            value,
            size=size,
            color=COLORS["evidence_text"],
            align="left",
        ),
    ]


def diagram(elements: list[dict]) -> dict:
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"viewBackgroundColor": COLORS["white"], "gridSize": None},
        "files": {},
    }


def build_application_architecture() -> dict:
    elements: list[dict] = []

    elements.extend(
        [
            text("app-title", 80, 38, 1440, "FOLIAR DISEASE DIAGNOSTIC APPLICATION ARCHITECTURE", size=30, color=COLORS["title"]),
            text(
                "app-subtitle",
                240,
                86,
                1120,
                "Image request flow across frontend UI, orchestration API, and specialized services",
                size=16,
                color=COLORS["body"],
            ),
            rectangle(
                "service-region",
                54,
                440,
                1492,
                500,
                fill=COLORS["white"],
                stroke=COLORS["body"],
                dashed=True,
                stroke_width=1,
            ),
            text(
                "service-region-label",
                78,
                458,
                620,
                "INFERENCE, DATA & KNOWLEDGE TIER",
                size=18,
                color=COLORS["title"],
                align="left",
            ),
        ]
    )

    # Main flow and fan-out arrows are drawn before nodes so they stay behind the boxes.
    elements.extend(
        [
            arrow("user-to-next", (278, 250), (400, 250), color=COLORS["start_stroke"], width=3),
            arrow("next-to-api", (690, 250), (790, 250), color=COLORS["primary_stroke"], width=3),
            arrow("api-to-onnx", (860, 320), (225, 555), color=COLORS["ai_stroke"]),
            arrow("api-to-postgres", (900, 320), (610, 555), color=COLORS["primary_stroke"]),
            arrow("api-to-minio", (960, 320), (995, 555), color=COLORS["warning_stroke"]),
            arrow("api-to-kb", (1010, 320), (1370, 555), color=COLORS["success_stroke"]),
        ]
    )

    elements.append(ellipse("user", 78, 195, 200, 110, fill=COLORS["start_fill"], stroke=COLORS["start_stroke"]))
    elements.append(text("user-text", 98, 226, 160, "User\nBrowser", size=18))
    elements.extend(
        box_with_text(
            "nextjs",
            400,
            190,
            290,
            120,
            "Next.js Frontend\nUpload • Results • History",
            fill=COLORS["primary_fill"],
            stroke=COLORS["primary_stroke"],
        )
    )
    elements.extend(
        box_with_text(
            "fastapi",
            790,
            180,
            300,
            140,
            "FastAPI Backend\nAuth • Orchestration • API",
            fill=COLORS["success_fill"],
            stroke=COLORS["success_stroke"],
            size=20,
        )
    )
    elements.extend(
        evidence(
            "api-contract",
            1160,
            160,
            350,
            "POST /api/v1/predict\nGET  /api/v1/knowledge\nPOST /api/v1/auth\nGET  /api/v1/history",
            size=14,
        )
    )
    elements.extend(
        [
            text("user-next-label", 292, 218, 100, "HTTPS", size=13, color=COLORS["body"]),
            text("next-api-label", 688, 218, 104, "HTTP / JSON", size=13, color=COLORS["body"]),
            text("onnx-arrow-label", 410, 392, 190, "Preprocessed Image", size=13, color=COLORS["ai_stroke"]),
            text("db-arrow-label", 650, 392, 170, "SQLModel / ORM", size=13, color=COLORS["primary_stroke"]),
            text("minio-arrow-label", 945, 392, 150, "Store / Read Image", size=13, color=COLORS["warning_stroke"]),
            text("kb-arrow-label", 1160, 392, 210, "Lookup Recommendations", size=13, color=COLORS["success_stroke"]),
        ]
    )

    service_specs = [
        (
            "onnx",
            90,
            "ONNX Runtime\nYOLO26-seg quantized",
            COLORS["ai_fill"],
            COLORS["ai_stroke"],
            "/models/yolo26_quantized.onnx\nTop-K • confidence • latency_ms",
        ),
        (
            "postgres",
            475,
            "PostgreSQL\nUsers • Diagnostic History",
            COLORS["primary_fill"],
            COLORS["primary_stroke"],
            "users • images • predictions\nSQLModel persistence",
        ),
        (
            "minio",
            860,
            "MinIO S3 Storage\nUploaded Leaf Images",
            COLORS["warning_fill"],
            COLORS["warning_stroke"],
            "bucket: plant-disease-images\npresigned image URL",
        ),
        (
            "knowledge",
            1245,
            "Expert Knowledge Base\nAgronomic Recommendations",
            COLORS["success_fill"],
            COLORS["success_stroke"],
            "backend/app/knowledge/diseases.json\nsymptoms • treatment • prevention",
        ),
    ]
    for element_id, x, label, fill, stroke, proof in service_specs:
        elements.extend(box_with_text(element_id, x, 555, 270, 130, label, fill=fill, stroke=stroke, size=18))
        elements.extend(evidence(f"{element_id}-evidence", x, 724, 270, proof, size=13))

    elements.extend(
        [
            text(
                "app-result",
                470,
                880,
                660,
                "Response: Disease label + Confidence + Top-K + Image URL + Recommendation",
                size=16,
                color=COLORS["body"],
            ),
            arrow("result-feedback", (1115, 868), (690, 330), color=COLORS["body"], dashed=True),
        ]
    )
    return diagram(elements)


def build_deployment_architecture() -> dict:
    elements: list[dict] = []

    elements.extend(
        [
            text("deploy-title", 80, 30, 1760, "GCP / K3S CLOUD DEPLOYMENT ARCHITECTURE", size=30, color=COLORS["title"]),
            text(
                "deploy-subtitle",
                280,
                76,
                1360,
                "From GitHub Actions and GHCR to Traefik, application workloads, and persistent storage",
                size=16,
                color=COLORS["body"],
            ),
            rectangle(
                "gcp-boundary",
                330,
                245,
                1510,
                920,
                fill=COLORS["white"],
                stroke=COLORS["primary_stroke"],
                dashed=True,
                stroke_width=2,
            ),
            text("gcp-label", 355, 262, 330, "GCP VM • Ubuntu 22.04 LTS", size=20, color=COLORS["title"], align="left"),
            rectangle(
                "k3s-boundary",
                375,
                310,
                1420,
                810,
                fill=COLORS["white"],
                stroke=COLORS["secondary_stroke"],
                dashed=True,
                stroke_width=2,
            ),
            text(
                "k3s-label", 400, 327, 360, "k3s • containerd • Helm", size=18, color=COLORS["subtitle"], align="left"
            ),
            rectangle(
                "namespace-boundary",
                420,
                375,
                1330,
                690,
                fill=COLORS["white"],
                stroke=COLORS["body"],
                dashed=True,
                stroke_width=1,
            ),
            text(
                "namespace-label",
                445,
                392,
                430,
                "namespace: plant-disease",
                size=17,
                color=COLORS["body"],
                align="left",
            ),
        ]
    )

    # Delivery pipeline across the top.
    elements.extend(
        [
            arrow("actions-to-ghcr", (600, 170), (740, 170), color=COLORS["primary_stroke"], width=3),
            arrow("ghcr-to-helm", (980, 170), (1100, 170), color=COLORS["primary_stroke"], width=3),
            arrow("helm-to-cluster", (1370, 200), (1460, 405), color=COLORS["success_stroke"], width=3),
        ]
    )
    elements.extend(
        box_with_text(
            "github-actions",
            330,
            115,
            270,
            110,
            "GitHub Actions\nLint • Test • Build",
            fill=COLORS["primary_fill"],
            stroke=COLORS["primary_stroke"],
            size=18,
        )
    )
    elements.extend(
        box_with_text(
            "ghcr",
            740,
            115,
            240,
            110,
            "GHCR\nDocker images",
            fill=COLORS["ai_fill"],
            stroke=COLORS["ai_stroke"],
            size=18,
        )
    )
    elements.extend(
        box_with_text(
            "helm",
            1100,
            115,
            270,
            110,
            "Helm qua SSH\nUpgrade • Rollout",
            fill=COLORS["success_fill"],
            stroke=COLORS["success_stroke"],
            size=18,
        )
    )
    elements.extend(
        evidence("pipeline-proof", 1445, 105, 360, "deploy.yml\nbuild → push → deploy → smoke test", size=14)
    )

    # Public request path.
    elements.extend(
        [
            arrow("internet-to-domain", (205, 540), (300, 540), color=COLORS["start_stroke"], width=3),
            arrow("domain-to-ingress", (425, 540), (515, 540), color=COLORS["start_stroke"], width=3),
            arrow("ingress-to-frontend", (755, 505), (870, 485), color=COLORS["primary_stroke"], width=3),
            arrow("ingress-to-backend", (755, 575), (870, 650), color=COLORS["success_stroke"], width=3),
        ]
    )
    elements.append(
        ellipse("internet-user", 30, 485, 175, 110, fill=COLORS["start_fill"], stroke=COLORS["start_stroke"])
    )
    elements.append(text("internet-user-text", 50, 517, 135, "Internet\nUsers", size=18))
    elements.extend(
        box_with_text(
            "duckdns",
            300,
            485,
            125,
            110,
            "DuckDNS\nHTTPS",
            fill=COLORS["decision_fill"],
            stroke=COLORS["decision_stroke"],
            size=16,
        )
    )
    elements.extend(
        box_with_text(
            "traefik",
            515,
            475,
            240,
            130,
            "Traefik Ingress\nTLS • Routing",
            fill=COLORS["decision_fill"],
            stroke=COLORS["decision_stroke"],
            size=18,
        )
    )
    elements.extend(
        evidence(
            "route-proof",
            515,
            630,
            240,
            "/        → frontend:3000\n/api/v1 → backend:8000\n/docs    → backend:8000",
            size=13,
        )
    )

    # Application workloads.
    elements.extend(
        box_with_text(
            "frontend-pod",
            870,
            435,
            270,
            120,
            "Frontend Deployment\nNext.js • port 3000",
            fill=COLORS["primary_fill"],
            stroke=COLORS["primary_stroke"],
            size=18,
        )
    )
    elements.extend(
        box_with_text(
            "backend-pod",
            870,
            605,
            270,
            135,
            "Backend Deployment\nFastAPI + ONNX Runtime",
            fill=COLORS["success_fill"],
            stroke=COLORS["success_stroke"],
            size=18,
        )
    )
    elements.extend(
        evidence("backend-proof", 870, 765, 270, "/health • /api/v1\nMODEL_PATH=/models/yolo26_quantized.onnx", size=13)
    )

    # Backend fan-out.
    elements.extend(
        [
            arrow("backend-to-postgres", (1140, 635), (1260, 500), color=COLORS["primary_stroke"]),
            arrow("backend-to-minio", (1140, 670), (1260, 670), color=COLORS["warning_stroke"]),
            arrow("backend-to-redis", (1140, 705), (1260, 840), color=COLORS["body"], dashed=True),
            arrow("model-pvc-to-backend", (1040, 985), (1010, 740), color=COLORS["ai_stroke"], width=3),
        ]
    )
    elements.extend(
        box_with_text(
            "postgres-workload",
            1260,
            445,
            300,
            120,
            "PostgreSQL StatefulSet\nUser Data & Diagnostic History",
            fill=COLORS["primary_fill"],
            stroke=COLORS["primary_stroke"],
            size=17,
        )
    )
    elements.extend(
        box_with_text(
            "minio-workload",
            1260,
            610,
            300,
            120,
            "MinIO StatefulSet\nLeaf Images & Object URLs",
            fill=COLORS["warning_fill"],
            stroke=COLORS["warning_stroke"],
            size=17,
        )
    )
    elements.extend(
        box_with_text(
            "redis-workload",
            1260,
            775,
            300,
            120,
            "Redis StatefulSet\nCaching Service",
            fill=COLORS["secondary_fill"],
            stroke=COLORS["secondary_stroke"],
            size=17,
        )
    )

    # Persistent storage row.
    elements.extend(
        [
            arrow("postgres-to-pvc", (1410, 565), (1410, 930), color=COLORS["primary_stroke"], dashed=True),
            arrow("minio-to-pvc", (1460, 730), (1600, 930), color=COLORS["warning_stroke"], dashed=True),
        ]
    )
    elements.extend(
        box_with_text(
            "model-pvc",
            825,
            930,
            285,
            100,
            "Model PVC • 10 GiB\nmount: /models",
            fill=COLORS["ai_fill"],
            stroke=COLORS["ai_stroke"],
            size=16,
        )
    )
    elements.extend(
        box_with_text(
            "postgres-pvc",
            1260,
            930,
            260,
            100,
            "PostgreSQL PVC\n20 GiB",
            fill=COLORS["primary_fill"],
            stroke=COLORS["primary_stroke"],
            size=16,
        )
    )
    elements.extend(
        box_with_text(
            "minio-pvc",
            1540,
            930,
            180,
            100,
            "MinIO PVC\n30 GiB",
            fill=COLORS["warning_fill"],
            stroke=COLORS["warning_stroke"],
            size=16,
        )
    )

    elements.extend(
        [
            text(
                "runtime-note",
                470,
                1080,
                1220,
                "Verified Runtime: Nodes Ready • Workloads Running • Ingress 80/443 • Helm Deployed",
                size=16,
                color=COLORS["success_stroke"],
            ),
            text("routing-front-label", 770, 460, 90, "route /", size=12, color=COLORS["primary_stroke"]),
            text("routing-api-label", 765, 590, 105, "route /api", size=12, color=COLORS["success_stroke"]),
        ]
    )
    return diagram(elements)


def _write_diagram(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate_all(output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    application_path = output_dir / "architecture_diagram.excalidraw"
    deployment_path = output_dir / "deployment_architecture_diagram.excalidraw"
    _write_diagram(application_path, build_application_architecture())
    _write_diagram(deployment_path, build_deployment_architecture())
    return application_path, deployment_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "docs",
        help="Directory that receives both .excalidraw files (default: repo/docs)",
    )
    args = parser.parse_args()
    for path in generate_all(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
