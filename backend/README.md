# Backend Service — Architecture, API & Serving Documentation

FastAPI asynchronous backend application providing real-time leaf disease instance segmentation inference, expert agricultural recommendations, user authentication with Redis token revocation, rate limiting, and diagnosis audit logging.

---

## 1. Architecture Overview

The backend is built with FastAPI, SQLModel (SQLAlchemy 2.0), PostgreSQL, MinIO, and Redis:

- **Authentication & RBAC (`backend/app/routers/auth.py`)**: User registration, login, JWT bearer authentication, and Redis-backed token revocation on logout.
- **Inference & Segmentation Service (`backend/app/routers/predict.py`, `backend/app/services/inference.py`)**:
  - Real-time foliar disease inference utilizing ONNX Runtime for YOLO26-seg models (both FP32 baseline and INT8 quantized checkpoints at $1024 \times 1024$ resolution).
  - Matrix decoding of prototype masks ($[1, 32, 256, 256]$) and 32 mask coefficients into polygon contours.
  - Transparent overlay rendering using OpenCV (`cv2`) with disease-specific color maps.
  - S3 upload to MinIO (`annotated_image_url`) with transactional cleanup for orphaned storage artifacts.
- **Agricultural Knowledge Base (`backend/app/routers/knowledge.py`, `backend/app/knowledge/knowledge_base.py`)**:
  - Bilingual agronomic advisory (Vietnamese & English) covering etiology, symptoms, chemical/biological treatments, prevention, and confidence-calibrated guidance.
  - Cached in Redis with 3600-second TTL.
- **Audit & History (`backend/app/routers/history.py`)**:
  - Secure, paginated retrieval of past diagnostic sessions.
  - Preserves both original leaf images, annotated segmentation masks, and detected lesion polygon structures.
- **Object Storage (`backend/app/services/storage.py`)**: MinIO S3-compatible client for persisting raw uploads and annotated image masks.
- **Caching & Throttling (`backend/app/services/cache.py`, `backend/app/services/limiter.py`)**:
  - Redis connection pooling with graceful in-memory fallback.
  - Sliding-window atomic rate limiting (`30 req/min` for inference, `10 req/min` for auth) returning `429 Too Many Requests` with `Retry-After` headers.
  - Token blacklisting with automatic TTL expiration matching the JWT expiration.

---

## 2. Infrastructure Services

To spin up all backend dependencies locally, run:

```bash
docker compose up -d postgres redis minio mlflow
```

### Endpoints:
- **PostgreSQL**: `localhost:5433` (mapped from container 5432; User: `admin`, Password: `changeme`, Database: `plant_disease`).
- **Redis**: `localhost:6379`.
- **MinIO API**: `localhost:9000` (Access Key: `minioadmin`, Secret Key: `minioadmin`).
- **MinIO Console**: `localhost:9001`.
- **MLflow Tracking**: `http://localhost:5001`.

---

## 3. Database Schema & Alembic Migrations

The database models are defined using SQLModel in `backend/app/db/orm_models.py`:

- `users`: User account credentials and timestamps (`id`, `username`, `email`, `hashed_password`, `created_at`).
- `images`: Image metadata and MinIO storage paths (`id`, `user_id`, `s3_path`, `content_type`, `created_at`).
- `predictions`: Model predictions, confidence scores, latencies, and expert recommendations (`id`, `user_id`, `image_id`, `predicted_label`, `confidence`, `top_k`, `latency_ms`, `recommendation`).

### Running Migrations

Database schema revisions are managed using Alembic in `backend/alembic/`:

```bash
# Apply all pending migrations to the database
uv run alembic -c backend/alembic.ini upgrade head

# Generate a new migration revision after modifying orm_models.py
uv run alembic -c backend/alembic.ini revision --autogenerate -m "describe_changes"
```

---

## 4. API Response Contracts

### `POST /api/v1/predict` (Foliar Disease Diagnosis)
Returns top-K classification probabilities, expert agronomic advisory, and detected segmentation masks:

```json
{
  "predicted_label": "LeafBlast",
  "confidence": 0.8842,
  "top_k": [
    {"label": "LeafBlast", "confidence": 0.8842},
    {"label": "BrownSpot", "confidence": 0.0815},
    {"label": "Healthy", "confidence": 0.0343}
  ],
  "recommendation": {
    "label": "LeafBlast",
    "name_en": "Rice Leaf Blast",
    "name_vi": "Bệnh đạo ôn lá lúa",
    "crop": "Rice",
    "severity": "High",
    "description": "...",
    "description_vi": "...",
    "symptoms": ["..."],
    "symptoms_vi": ["..."],
    "treatments": ["..."],
    "treatments_vi": ["..."],
    "prevention": ["..."],
    "prevention_vi": ["..."],
    "confidence_note_vi": "...",
    "advisory_vi": "..."
  },
  "latency_ms": 164.5,
  "image_id": 142,
  "image_url": "http://localhost:9000/plant-disease-images/user_1/leaf_142.jpg",
  "annotated_image_url": "http://localhost:9000/plant-disease-images/user_1/annotated_leaf_142.jpg",
  "detections": [
    {
      "label": "LeafBlast",
      "confidence": 0.8842,
      "box": [128.0, 245.0, 310.0, 480.0],
      "class_id": 6,
      "polygon": [[130, 250], [180, 245], [300, 310], [280, 470], [140, 460]],
      "mask_area_ratio": 0.064
    }
  ]
}
```

---

## 5. Environment Variables Configuration

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `APP_ENV` | `production` | Environment mode (`development`, `production`, `testing`) |
| `SECRET_KEY` | `change-me-in-production` | Secret key for signing JWT authentication tokens |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` | JWT expiration duration in minutes (24 hours) |
| `SKIP_DB_INIT` | `false` | When true, skips initial SQLModel table creation |
| `MODEL_PATH` | `/models/yolo26_quantized.onnx` | Path to INT8 or FP32 ONNX segmentation checkpoint |
| `CLASS_NAMES_PATH` | `/models/class_names.json` | Path to class mapping JSON file |
| `MODEL_INPUT_SIZE` | `1024` | Input spatial dimension for inference ($1024 \times 1024$) |
| `MODEL_VERSION` | `yolo26-seg-onnx` | Version identifier reported in health checks |
| `POSTGRES_HOST` | `postgres` | Hostname of the PostgreSQL database |
| `POSTGRES_PORT` | `5432` | Port of the PostgreSQL database |
| `POSTGRES_DB` | `plant_disease` | Relational database name |
| `POSTGRES_USER` | `admin` | Database username |
| `POSTGRES_PASSWORD` | `changeme` | Database password |
| `REDIS_URL` | `redis://redis:6379/0` | Connection string for Redis instance |
| `REDIS_ENABLED` | `true` | Enables/disables caching and rate limiting |
| `RATE_LIMIT_PREDICT_PER_MINUTE` | `30` | Max inference requests allowed per IP per minute |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | `10` | Max login attempts allowed per IP per minute |
| `KNOWLEDGE_CACHE_TTL_SECONDS` | `3600` | Redis cache expiration for knowledge base responses |
| `MINIO_ENDPOINT` | `minio:9000` | S3 endpoint URL for image uploads |
| `MINIO_ACCESS_KEY` | `minioadmin` | MinIO root access key |
| `MINIO_SECRET_KEY` | `minioadmin` | MinIO root secret key |
| `MINIO_BUCKET` | `plant-disease-images`| Bucket for storing uploaded and annotated imagery |
| `MINIO_SECURE` | `false` | Set to true when terminating TLS directly on MinIO |
| `MLFLOW_TRACKING_URI` | `http://mlflow:5000` | Centralized MLflow server tracking URI |

---

## 6. Running the Backend Server

```bash
# Start FastAPI with hot reload on port 8000
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation is accessible at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

---

## 7. Automated Tests

```bash
# Run all unit, service, cache, rate limiter, and API integration tests
uv run pytest tests/test_knowledge_base.py \
              tests/test_knowledge_api.py \
              tests/test_cache_service.py \
              tests/test_rate_limiter.py \
              tests/test_inference_logic.py \
              tests/integration/ -v
```
