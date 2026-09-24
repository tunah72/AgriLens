# AgriLens Deployment Architecture & Guides

This directory contains configuration templates, Kubernetes Helm charts, environment blueprints, and deployment scripts for **AgriLens**.

---

## 1. Deployment Strategies

AgriLens supports two primary deployment topologies:

### Topology A: Single-Node VM / AWS EC2 (Docker Compose) — *Recommended for Production Launch*
For deploying the complete full-stack platform (Next.js Frontend, FastAPI Backend, PostgreSQL 16, Redis 7, MinIO S3, and MLflow 2.16) on a single AWS EC2 virtual machine (`c6i.large` or `t3.large`):
- Refer to the detailed runbook: **[`docs/DEPLOYMENT_EC2.md`](../docs/DEPLOYMENT_EC2.md)**
- Stack definition: **[`docker-compose.yml`](../docker-compose.yml)**
- Environment template: **[`deployment/.env.example`](.env.example)**

### Topology B: Multi-Node Kubernetes / K3s (Helm Chart)
For deploying on a lightweight Kubernetes cluster (K3s) with automated ingress routing, persistent volume claims, and cluster scaling:
- Helm Chart definition: **[`deployment/helm/Chart.yaml`](helm/Chart.yaml)**
- Configurable values: **[`deployment/helm/values.yaml`](helm/values.yaml)**
- Storage verification script: **[`deployment/scripts/verify-storage.sh`](scripts/verify-storage.sh)**
- K3s bootstrap script: **[`deployment/scripts/setup-k3s.sh`](scripts/setup-k3s.sh)**
- Traefik ingress proxy: **[`deployment/traefik/traefik.yml`](traefik/traefik.yml)**

---

## 2. Infrastructure Services Summary

| Service | Port | Internal DNS | Role |
| :--- | :---: | :--- | :--- |
| **Frontend** | `3000` | `frontend` | Next.js 15 presentation layer with segmentation visualizer |
| **Backend** | `8000` | `backend` | FastAPI REST API & ONNX Runtime instance segmentation engine |
| **PostgreSQL**| `5433:5432` | `postgres` | User credentials, image metadata, and diagnostic records |
| **Redis** | `6379` | `redis` | Knowledge base cache, sliding-window rate limiting, token blacklist |
| **MinIO** | `9000 / 9001`| `minio` | S3-compatible storage for raw foliage photos and segmentation masks |
| **MLflow** | `5001:5000` | `mlflow` | Centralized experiment tracking, training curves, and artifact registry |

---

## 3. Quick EC2 Deployment Summary

```bash
# 1. Clone repository
git clone https://github.com/hcmus-ml-plant-disease-detection/plant-disease.git agrilens
cd agrilens

# 2. Configure environment
cp .env.example .env
# Edit .env and set NEXT_PUBLIC_API_BASE_URL=http://<EC2_PUBLIC_IP>:8000/api/v1

# 3. Launch stack
docker compose up -d --build

# 4. Apply database migrations
docker compose exec backend alembic upgrade head
```

For complete instructions including Nginx reverse proxy configuration, Let's Encrypt SSL automation, and MLflow experiment imports, see **[`docs/DEPLOYMENT_EC2.md`](../docs/DEPLOYMENT_EC2.md)**.
