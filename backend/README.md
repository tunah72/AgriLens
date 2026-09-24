# Backend Service — Setup and Database Documentation

FastAPI backend application providing leaf disease instance segmentation inference, expert agricultural recommendations, user authentication, and diagnosis audit logging.

---

## 1. Architecture Overview

The backend is built with FastAPI, SQLModel (SQLAlchemy 2.0), PostgreSQL, MinIO, and Redis:

- **Authentication & RBAC (`backend/app/routers/auth.py`)**: User registration, login, JWT bearer authentication, and Redis-backed token revocation / logout.
- **Inference Service (`backend/app/routers/predict.py`)**: Real-time foliar disease inference utilizing ONNX Runtime for YOLO26-seg models, protected by Redis rate limiting.
- **Agricultural Knowledge Base (`backend/app/routers/knowledge.py`)**: Disease descriptions, symptoms, causes, remedies, prevention measures, and literature citations with Redis caching.
- **Audit & History (`backend/app/routers/history.py`)**: Secure pagination of diagnostic sessions and user-submitted leaf images.
- **Object Storage (`backend/app/services/storage.py`)**: MinIO S3-compatible client for storing raw uploads and annotated image masks.
- **Caching & Throttling (`backend/app/services/cache.py`, `backend/app/services/limiter.py`)**: Redis connection pooling with graceful fallback, atomic rate limiting, and JSON object caching.
---

## 2. Local Infrastructure Services

To spin up PostgreSQL, MinIO, and Redis for local backend development, run the following command from the repository root:

```bash
docker compose up -d postgres minio redis
```

### Service Endpoints
- **PostgreSQL**: `localhost:5432` (Username: `admin`, Password: `changeme`, Database: `plant_disease`).
- **MinIO API**: `localhost:9000` (Access Key: `minioadmin`, Secret Key: `minioadmin`).
- **MinIO Console**: `localhost:9001`.
- **Redis**: `localhost:6379`.

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

## 4. Running the Backend Server

```bash
# Start FastAPI with hot reload on port 8000
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive documentation is accessible at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

---

## 5. Automated Tests

```bash
# Run all backend unit and API integration tests
uv run pytest tests/test_knowledge_base.py tests/test_knowledge_api.py -v
```
