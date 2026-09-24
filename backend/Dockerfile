FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /app
# Cài system dependencies cho OpenCV (cv2)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Cài uv
COPY --from=ghcr.io/astral-sh/uv:0.11.0 /uv /uvx /bin/

# Cài dependencies (chỉ nhóm backend)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --only-group backend --no-install-project --compile-bytecode

# Copy source code
COPY backend ./backend
COPY alembic.ini ./alembic.ini
COPY models /models
COPY artifacts/yolo26_seg_joint/yolo26n_seg_joint_int8.onnx /models/yolo26_quantized.onnx
EXPOSE 8000

# Chạy migration rồi mới khởi động server
CMD ["sh", "-c", "alembic upgrade head && uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]
