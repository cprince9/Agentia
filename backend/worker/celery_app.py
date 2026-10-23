import asyncio
import structlog
from celery import Celery
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from redis.asyncio import from_url as redis_from_url

from ..config.settings import get_settings
from ..services.event_bus import EventBus
from ..rag.retriever import RAGRetriever
from ..sandbox.executor import SandboxExecutor
from ..graph.runner import run_pipeline

logger = structlog.get_logger(__name__)
settings = get_settings()

app = Celery(
    "masds",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)


@app.task(bind=True, max_retries=3, name="masds.run_pipeline")
def run_pipeline_task(self, session_id: str, requirement: str):
    """
    Celery background worker task for running the MASDS development pipeline.
    """
    logger.info("celery_task_started", task_id=self.request.id, session_id=session_id)

    async def _execute():
        # Setup async DB engine & session
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        # Setup Redis & EventBus
        redis_client = redis_from_url(settings.REDIS_URL, decode_responses=False)
        event_bus = EventBus(redis=redis_client)

        rag = RAGRetriever()
        sandbox = SandboxExecutor(settings=settings)

        try:
            async with session_factory() as session:
                result_state = await run_pipeline(
                    session_id=session_id,
                    requirement=requirement,
                    db=session,
                    settings=settings,
                    event_bus=event_bus,
                    rag_retriever=rag,
                    sandbox_executor=sandbox,
                )
                return {
                    "session_id": session_id,
                    "status": result_state.get("pipeline_status"),
                    "staging_url": result_state.get("staging_url"),
                    "code_files_count": len(result_state.get("code_files", [])),
                }
        finally:
            await redis_client.aclose()
            await engine.dispose()

    try:
        return asyncio.run(_execute())
    except Exception as exc:
        logger.error("celery_task_error", session_id=session_id, error=str(exc))
        raise self.retry(exc=exc, countdown=10)
