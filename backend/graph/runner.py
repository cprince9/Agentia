import uuid
from datetime import datetime, timezone
from typing import Optional, Any
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from .state import AgentState
from .builder import build_pipeline
from ..config.settings import Settings, get_settings
from ..services.event_bus import EventBus
from ..rag.retriever import RAGRetriever
from ..sandbox.executor import SandboxExecutor
from ..db import crud

logger = structlog.get_logger(__name__)


async def run_pipeline(
    session_id: str,
    requirement: str,
    db: AsyncSession,
    settings: Optional[Settings] = None,
    event_bus: Optional[EventBus] = None,
    rag_retriever: Optional[RAGRetriever] = None,
    sandbox_executor: Optional[SandboxExecutor] = None,
) -> AgentState:
    """
    Execute the end-to-end multi-agent pipeline for a development session.
    Persists progress, artifacts, and execution metrics to the database and event bus.
    """
    settings = settings or get_settings()
    rag = rag_retriever or RAGRetriever()
    sandbox = sandbox_executor or SandboxExecutor(settings)

    logger.info("starting_pipeline_execution", session_id=session_id)

    # 1. Update session to running
    await crud.update_session_status(db, session_id, "running")
    if event_bus:
        await event_bus.publish(
            session_id=session_id,
            event_type="PIPELINE_STARTED",
            payload={"requirement": requirement},
        )

    # 2. Build initial state
    initial_state: AgentState = {
        "session_id": session_id,
        "requirement": requirement,
        "project_plan": None,
        "architecture": None,
        "code_files": [],
        "current_module_index": 0,
        "coder_attempt": 0,
        "test_files": [],
        "test_results": None,
        "review_result": None,
        "review_cycle": 0,
        "devops_artifacts": [],
        "staging_url": None,
        "pipeline_status": "running",
        "error_log": [],
        "agent_messages": [],
        "current_agent": "system",
    }

    # 3. Compile graph
    compiled_graph = build_pipeline(
        settings=settings,
        event_bus=event_bus,
        rag_retriever=rag,
        sandbox_executor=sandbox,
    )

    final_state: AgentState = initial_state

    try:
        # Run graph asynchronously
        final_state = await compiled_graph.ainvoke(initial_state)

        # Evaluate final status
        status = final_state.get("pipeline_status", "completed")
        staging_url = final_state.get("staging_url")

        if status == "failed":
            error_summary = "\n".join(final_state.get("error_log", ["Pipeline failed"]))
            await crud.update_session_status(
                db,
                session_id,
                "failed",
                error=error_summary,
            )
            if event_bus:
                await event_bus.publish(
                    session_id=session_id,
                    event_type="PIPELINE_FAILED",
                    payload={"error": error_summary},
                )
        else:
            # Save all generated code files and devops artifacts in DB
            all_files = list(final_state.get("code_files", [])) + list(final_state.get("devops_artifacts", []))
            for cf in all_files:
                try:
                    await crud.create_artifact(
                        db=db,
                        session_id=session_id,
                        file_path=cf.path,
                        file_type=cf.language,
                        s3_key=f"sessions/{session_id}/{cf.path}",
                        size_bytes=len(cf.content.encode("utf-8")),
                    )
                except Exception as art_err:
                    logger.warning("save_artifact_db_error", file=cf.path, error=str(art_err))

            # Mark session as completed
            await crud.update_session_status(
                db,
                session_id,
                "completed",
                staging_url=staging_url,
                completed_at=datetime.now(timezone.utc),
            )
            logger.info("pipeline_completed_successfully", session_id=session_id, staging_url=staging_url)

        return final_state

    except Exception as e:
        logger.error("pipeline_fatal_exception", session_id=session_id, error=str(e))
        error_msg = str(e)
        final_state["pipeline_status"] = "failed"
        final_state["error_log"].append(error_msg)

        await crud.update_session_status(
            db,
            session_id,
            "failed",
            error=error_msg,
        )
        if event_bus:
            await event_bus.publish(
                session_id=session_id,
                event_type="PIPELINE_FAILED",
                payload={"error": error_msg},
            )
        return final_state
