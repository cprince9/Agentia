import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from redis.asyncio import from_url as redis_from_url

from .config.settings import get_settings
from .db.models import Base
from .api.dependencies import get_engine
from .api.routes import sessions_router, artifacts_router, ws_router
from .rag.ingestor import DocumentIngestor
from .rag.retriever import RAGRetriever

logger = structlog.get_logger(__name__)
settings = get_settings()

# Initialize Rate Limiter: 5 pipeline runs per hour per client IP
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle management.
    Initializes database tables, verifies Redis, and warms up RAG vector knowledge base.
    """
    logger.info("masds_backend_starting_up", version="1.0.0")

    # 1. Initialize DB tables
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("database_tables_initialized")
    except Exception as e:
        logger.warning("database_initialization_warning", error=str(e))

    # 2. Test Redis connectivity
    try:
        redis = redis_from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.aclose()
        logger.info("redis_connected")
    except Exception as e:
        logger.warning("redis_connectivity_warning", error=str(e))

    # 3. Seed vector knowledge base if uninitialized
    try:
        retriever = RAGRetriever()
        ingestor = DocumentIngestor(retriever=retriever)
        await ingestor.ingest_default_knowledge_base()
        logger.info("knowledge_base_seeded")
    except Exception as e:
        logger.warning("rag_seeding_warning", error=str(e))

    yield

    # Shutdown
    logger.info("masds_backend_shutting_down")
    try:
        engine = get_engine()
        await engine.dispose()
    except Exception:
        pass


app = FastAPI(
    title="MASDS - Multi-Agent Software Development System",
    description="Autonomous End-to-End Multi-Agent Engineering Architecture Backend API",
    version="1.0.0",
    lifespan=lifespan,
)

# Register SlowAPI limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware (permits full access for development and frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Measure request latency and record access logs."""
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(
        "http_request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


# Include Routers
app.include_router(sessions_router, prefix="/api/v1")
app.include_router(artifacts_router, prefix="/api/v1")
app.include_router(ws_router)


@app.get("/health", tags=["system"])
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check validating API, Database, and Redis connectivity.
    """
    db_status = "ok"
    redis_status = "ok"

    # Test DB
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # Test Redis
    try:
        redis = redis_from_url(settings.REDIS_URL)
        await redis.ping()
        await redis.aclose()
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"

    overall_ok = (db_status == "ok" and redis_status == "ok")
    status_code = status.HTTP_200_OK if overall_ok else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ok" if overall_ok else "degraded",
            "db": db_status,
            "redis": redis_status,
            "version": "1.0.0",
        },
    )


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower(),
    )
