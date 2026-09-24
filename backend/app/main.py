"""
FastAPI Backend — Main application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.config import settings
from backend.app.db import init_db
from backend.app.routers import auth, history, knowledge, predict


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    if settings.SKIP_DB_INIT:
        yield
        return

    try:
        init_db()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    yield


tags_metadata = [
    {
        "name": "knowledge",
        "description": "Expert agricultural knowledge base for rice and coffee leaf diseases.",
    },
    {
        "name": "prediction",
        "description": "Real-time leaf disease diagnosis using YOLO26-seg (ONNX runtime).",
    },
    {
        "name": "auth",
        "description": "User account management, registration, authentication, and authorization.",
    },
    {
        "name": "history",
        "description": "Audit diagnosis history, uploaded images, and expert recommendations.",
    },
]


app = FastAPI(
    title="Plant Disease Detection API",
    description="End-to-End Plant Leaf Disease Diagnosis System (Coffee & Rice)",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(predict.router, prefix="/api/v1")
app.include_router(history.router, prefix="/api/v1")


@app.get("/")
async def root_redirect():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/api/v1")
async def api_v1_root():
    """Welcome endpoint for API v1."""
    return {
        "message": "Welcome to the Plant Disease Detection API v1",
        "docs": "/docs",
        "health": "/health",
        "version": "0.1.0",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint reporting system and dependency status."""
    from backend.app.services.cache import get_cache_service

    cache = get_cache_service()
    redis_status = "healthy" if cache.is_connected() else "disconnected"

    return {
        "status": "ok",
        "services": {
            "redis": redis_status,
        },
    }
