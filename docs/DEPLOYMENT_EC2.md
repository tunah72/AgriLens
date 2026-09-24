# AgriLens — AWS EC2 Production Deployment Runbook

Comprehensive deployment guide for launching the **AgriLens** end-to-end foliar leaf disease instance segmentation platform on an **Amazon Web Services (AWS) EC2** virtual instance using Docker Compose, Nginx, and Let's Encrypt SSL.

---

## 1. System & Architecture Overview on EC2

```mermaid
flowchart TB
    InternetUser((Farmer / Agronomist Browser)) -->|HTTPS 443| Nginx[Nginx Reverse Proxy & TLS Termination]
    AdminUser((ML Engineer / Admin)) -->|VPN / Restricted IP: 5001, 9001| Nginx

    subgraph EC2["AWS EC2 Instance (Ubuntu 24.04 LTS)"]
        subgraph Proxy["Web Ingress Tier"]
            Nginx
        end

        subgraph DockerCompose["Docker Compose Stack"]
            subgraph WebApp["Presentation Tier"]
                Frontend["AgriLens Web UI (Next.js 15, Port 3000)"]
            end

            subgraph ApiTier["Application & Inference Tier"]
                Backend["FastAPI Backend Server (Port 8000)"]
                ONNX["ONNX Runtime Engine (YOLO26-seg INT8)"]
                SegRender["Mask Decoder & Contour Overlay (OpenCV)"]
                Backend --> ONNX
                Backend --> SegRender
            end

            subgraph CacheTier["Caching & Rate Limiting"]
                Redis["Redis 7 (Port 6379, Internal)"]
            end

            subgraph StorageTier["Persistence Tier"]
                Postgres[("PostgreSQL 16 (Port 5433:5432)")]
                MinIO[("MinIO S3 Storage (API: 9000, Console: 9001)")]
            end

            subgraph MLOpsTier["MLOps Tier"]
                MLflow["MLflow Tracking Server (Port 5001:5000)"]
            end
        end
    end

    Nginx -->|/ (Root UI)| Frontend
    Nginx -->|/api/* & /docs| Backend
    Backend --> Redis
    Backend --> Postgres
    Backend --> MinIO
    Frontend -.->|Client Browser API calls| Nginx
```

---

## 2. AWS EC2 Sizing & Provisioning Specifications

### 2.1. Recommended Instance Types

| Spec | Recommended (Production) | Budget / Development | Notes |
| :--- | :--- | :--- | :--- |
| **Instance Type** | **`c6i.large`** or **`c7i.large`** | **`t3.large`** (or `t3.medium` + swap) | Compute-optimized instances yield consistent ~160ms ONNX inference. |
| **vCPU** | 2 vCPUs | 2 vCPUs | Dedicated CPU cores avoid burst throttling during continuous inference. |
| **RAM** | 4 GiB | 4 – 8 GiB | 4 GiB physical RAM is sufficient with 4 GiB swap file enabled. |
| **Storage (EBS)** | **40 GiB gp3** (3000 IOPS, 125 MB/s) | 30 GiB gp3 | Houses Docker images, models, PostgreSQL data, and MinIO uploads. |
| **Operating System** | **Ubuntu Server 24.04 LTS** (64-bit x86_64) | Ubuntu 22.04 LTS | Standard long-term support distribution. |

> **Pro-Tip**: Allocate an **AWS Elastic IP (EIP)** and associate it with your EC2 instance. Without an Elastic IP, your public IP will change whenever the instance stops or restarts, which will invalidate the frontend's baked API URL.

---

### 2.2. AWS Security Group Rules

Create a dedicated Security Group (e.g., `agrilens-production-sg`) with the following inbound traffic policies:

| Type | Port Range | Protocol | Source | Purpose |
| :--- | :---: | :---: | :--- | :--- |
| **SSH** | `22` | TCP | `My IP` (or Company VPN CIDR) | Secure administrative terminal access |
| **HTTP** | `80` | TCP | `0.0.0.0/0` | Let's Encrypt validation & HTTP-to-HTTPS redirect |
| **HTTPS** | `443` | TCP | `0.0.0.0/0` | Secure public web access for farmers/users |
| **Custom TCP (Direct UI)** | `3000` | TCP | `0.0.0.0/0` *(Optional without Nginx)* | Direct Next.js access during testing |
| **Custom TCP (Direct API)** | `8000` | TCP | `0.0.0.0/0` *(Optional without Nginx)* | Direct FastAPI access during testing |
| **Custom TCP (MLflow)** | `5001` | TCP | `My IP` / Admin CIDR Only | Restricted access to MLflow Experiment UI |
| **Custom TCP (MinIO Console)**| `9001` | TCP | `My IP` / Admin CIDR Only | Restricted access to MinIO S3 Console |

> **Security Warning**: **Never open ports `5433` (PostgreSQL) or `6379` (Redis) to `0.0.0.0/0`**. These database ports are accessed strictly inside the private Docker bridge network.

---

## 3. Host System Setup & Preparation

SSH into your freshly provisioned EC2 instance:

```bash
ssh -i /path/to/your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

### 3.1. Update System & Install Base Utilities
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y curl git ufw htop ca-certificates gnupg lsb-release
```

### 3.2. Configure a 4 GiB Swap Space
Creating swap prevents the Linux Out-Of-Memory (OOM) killer from terminating containers during Next.js production builds or concurrent model execution:

```bash
# Check if swap exists
sudo swapon --show

# Allocate 4GB swapfile
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Persist swap across reboots
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Optimize swappiness for server workloads
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

### 3.3. Install Docker Engine & Docker Compose Plugin
```bash
# Add Docker's official GPG key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# Set up Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker packages
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Grant ubuntu user docker execution privileges (requires re-login or newgrp)
sudo usermod -aG docker ubuntu
newgrp docker

# Verify Docker installation
docker version
docker compose version
```

---

## 4. Deploying AgriLens via Docker Compose

### 4.1. Clone the Codebase
```bash
cd /home/ubuntu
git clone https://github.com/hcmus-ml-plant-disease-detection/plant-disease.git agrilens
cd agrilens
```

### 4.2. Configure Production Environment Variables
Generate secure random passwords and configure the `.env` file:

```bash
cp .env.example .env
```

Edit `.env` using `nano .env`:
```bash
# 1. Generate a 32-byte hexadecimal secret key
openssl rand -hex 32
# -> Paste output into SECRET_KEY=...

# 2. Update database credentials
POSTGRES_USER=agrilens_admin
POSTGRES_PASSWORD=YOUR_STRONG_DB_PASSWORD_HERE

# 3. Update MinIO credentials
MINIO_USER=agrilens_minio
MINIO_PASSWORD=YOUR_STRONG_MINIO_PASSWORD_HERE

# 4. Configure Public API URL for the Frontend
# If accessing directly by IP:
NEXT_PUBLIC_API_BASE_URL=http://<YOUR_EC2_PUBLIC_IP>:8000/api/v1
# If deploying with a custom domain and HTTPS (recommended):
# NEXT_PUBLIC_API_BASE_URL=https://<YOUR_DOMAIN>/api/v1
```

### 4.3. Build & Launch the Complete Container Stack
Execute Docker Compose in detached mode:

```bash
docker compose up -d --build
```

### 4.4. Verify Container States & Health
Check that all 6 services report healthy status:

```bash
docker compose ps
```

Expected output:
```text
NAME                 IMAGE                         STATUS                    PORTS
agrilens-backend-1   agrilens-backend              Up (healthy)              0.0.0.0:8000->8000/tcp
agrilens-frontend-1  agrilens-frontend             Up (healthy)              0.0.0.0:3000->3000/tcp
agrilens-minio-1     minio/minio:latest            Up (healthy)              0.0.0.0:9000->9000/tcp, 0.0.0.0:9001->9001/tcp
agrilens-mlflow-1    ghcr.io/mlflow/mlflow:latest  Up                        0.0.0.0:5001->5000/tcp
agrilens-postgres-1  postgres:16-alpine            Up (healthy)              0.0.0.0:5433->5432/tcp
agrilens-redis-1     redis:7-alpine                Up (healthy)              0.0.0.0:6379->6379/tcp
```

### 4.5. Run Database Migrations
Run Alembic database migrations to create the required tables:

```bash
docker compose exec backend alembic upgrade head
```

Verify backend health endpoint:
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","model_version":"yolo26-seg-onnx","database":"connected","storage":"connected","cache":"connected"}
```

---

## 5. Synchronizing MLflow Experiments on EC2

To populate the MLflow tracking server with the benchmark results, training curves, and quantization audits:

```bash
# 1. Install uv on the host (if running scripts directly on host)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# 2. Run the importer scripts pointing to the MLflow container
uv run python scripts/import_experiments_to_mlflow.py --tracking-uri http://localhost:5001
uv run python scripts/log_mlflow_pipeline.py --tracking-uri http://localhost:5001
```

Now, navigate to `http://<EC2_PUBLIC_IP>:5001` to view the MLflow UI.

---

## 6. Production Reverse Proxy & SSL (Nginx + Let's Encrypt)

For enterprise-grade production, traffic should enter via standard ports 80/443, terminate TLS with valid SSL certificates, and proxy to the respective containers.

### 6.1. Install Nginx & Certbot
```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

### 6.2. Configure Nginx Virtual Host
Create `/etc/nginx/sites-available/agrilens`:

```bash
sudo nano /etc/nginx/sites-available/agrilens
```

Add the following configuration (replace `agrilens.yourdomain.com` with your domain or server IP):

```nginx
server {
    listen 80;
    server_name agrilens.yourdomain.com;

    # Maximum image upload size (15 MB to accommodate high-res leaf photos)
    client_max_body_size 15M;

    # Frontend Web App (Next.js)
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API & Health Endpoints
    location ~ ^/(api|docs|redoc|openapi.json|health) {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }

    # MinIO Storage Objects (Leaf & Mask Images)
    location /plant-disease-images/ {
        proxy_pass http://127.0.0.1:9000/plant-disease-images/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site configuration and test syntax:
```bash
sudo ln -s /etc/nginx/sites-available/agrilens /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

### 6.3. Obtain Free Automated SSL Certificate
```bash
sudo certbot --nginx -d agrilens.yourdomain.com
```

Certbot automatically configures TLS 1.3, sets up HTTPS redirects, and schedules automatic certificate renewals.

---

## 7. Operations & Troubleshooting Runbook

### 7.1. Viewing Real-Time Logs
```bash
# Follow logs for all services
docker compose logs -f

# Follow backend logs only
docker compose logs -f backend

# Follow frontend logs only
docker compose logs -f frontend
```

### 7.2. Inspecting Resource Utilization
```bash
# Check CPU, Memory, and Network I/O of all running containers
docker stats
```

### 7.3. Database & MinIO Data Backups
All persistent data resides in Docker volumes:
- `postgres_data`: PostgreSQL database tables (`users`, `images`, `predictions`).
- `minio_data`: Leaf photographs and segmentation mask PNGs.
- `redis_data`: Cache entries and token blacklist keys.
- `mlflow_data`: MLflow experiment database and artifact files.

**Perform a PostgreSQL backup:**
```bash
docker compose exec postgres pg_dump -U agrilens_admin plant_disease > backup_$(date +%Y%m%d).sql
```

**Restore a PostgreSQL backup:**
```bash
cat backup_20260924.sql | docker compose exec -T postgres psql -U agrilens_admin plant_disease
```

---

## 8. Common Pitfalls & Solutions Checklist

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| **Frontend displays "Network Error" or cannot connect to backend** | `NEXT_PUBLIC_API_BASE_URL` in `.env` is set to `localhost` or missing. | Update `NEXT_PUBLIC_API_BASE_URL=http://<EC2_PUBLIC_IP>:8000/api/v1` in `.env`, then rebuild frontend: `docker compose build --no-cache frontend && docker compose up -d frontend`. |
| **Container build fails with OOM (Exit 137)** | Next.js compilation exhausts memory on small EC2 instances. | Ensure the 4GB swapfile is created and active (`swapon --show`). |
| **Segmentation mask not displaying in UI** | MinIO URL is using container internal hostname `minio:9000` instead of public URL. | Configure `MINIO_ENDPOINT` or proxy MinIO requests through Nginx `/plant-disease-images/`. |
| **Rate limit 429 errors during testing** | Exceeded sliding window limit (30 requests/minute). | Wait 60 seconds or adjust `RATE_LIMIT_PREDICT_PER_MINUTE=100` in `.env` and restart backend. |
| **MLflow UI not loading** | Port 5001 is blocked by AWS Security Group. | Add inbound rule for port 5001 in your AWS EC2 Security Group restricted to your IP address. |
