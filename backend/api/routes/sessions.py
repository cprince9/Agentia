import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...db import crud
from ...db.models import Session
from ..dependencies import get_db, get_current_user
from ...worker.celery_app import run_pipeline_task

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionCreateRequest(BaseModel):
    requirement: str = Field(..., min_length=5, description="Software requirements specification")


class SessionCreateResponse(BaseModel):
    session_id: str
    status: str
    created_at: datetime


class AgentRunStatus(BaseModel):
    agent_name: str
    status: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    llm_model: Optional[str] = None


class SessionDetailResponse(BaseModel):
    id: str
    requirement: str
    status: str
    progress_percent: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    staging_url: Optional[str] = None
    error: Optional[str] = None
    agent_runs: List[AgentRunStatus] = []


class EventItemResponse(BaseModel):
    id: int
    session_id: str
    event_type: str
    agent_name: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: datetime


class EventsPaginationResponse(BaseModel):
    items: List[EventItemResponse]
    next_cursor: Optional[int] = None
    total_returned: int


def _calculate_progress(session: Session) -> int:
    if session.status == "completed":
        return 100
    if session.status == "pending":
        return 5

    # Check agent runs if available
    agent_weights = {
        "planner": 15,
        "architect": 30,
        "coder": 60,
        "tester": 80,
        "reviewer": 90,
        "devops": 98,
    }

    highest_progress = 10
    if hasattr(session, "agent_runs") and session.agent_runs:
        for run in session.agent_runs:
            if run.status == "completed":
                weight = agent_weights.get(run.agent_name.lower(), 10)
                highest_progress = max(highest_progress, weight)
            elif run.status == "running":
                weight = agent_weights.get(run.agent_name.lower(), 10) - 5
                highest_progress = max(highest_progress, weight)

    return min(highest_progress, 98)


@router.post("", response_model=SessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Create a new MASDS development session and enqueue background pipeline execution.
    """
    user_id = current_user.get("sub") if current_user else None
    session = await crud.create_session(db=db, requirement=request.requirement, user_id=user_id)

    session_id_str = str(session.id)
    try:
        # Enqueue Celery task
        run_pipeline_task.delay(session_id=session_id_str, requirement=session.requirement)
    except Exception as e:
        # Graceful logging if Celery/Redis broker is in local test mode
        pass

    return SessionCreateResponse(
        session_id=session_id_str,
        status=session.status,
        created_at=session.created_at,
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve session status, progress metrics, and associated agent execution records.
    """
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    session = await crud.get_session(db=db, session_id=sid, load_relations=True)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    progress = _calculate_progress(session)

    agent_run_list = [
        AgentRunStatus(
            agent_name=r.agent_name,
            status=r.status,
            started_at=r.started_at,
            ended_at=r.ended_at,
            llm_model=r.llm_model,
        )
        for r in getattr(session, "agent_runs", [])
    ]

    return SessionDetailResponse(
        id=str(session.id),
        requirement=session.requirement,
        status=session.status,
        progress_percent=progress,
        created_at=session.created_at,
        updated_at=session.updated_at,
        completed_at=session.completed_at,
        staging_url=session.staging_url,
        error=session.error,
        agent_runs=agent_run_list,
    )


@router.get("/{session_id}/events", response_model=EventsPaginationResponse)
async def get_session_events(
    session_id: str,
    cursor: int = Query(0, ge=0, description="Event ID cursor for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max events to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Paginated event history for a development session.
    """
    try:
        sid = uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    events = await crud.get_events(db=db, session_id=sid, cursor=cursor, limit=limit)

    items = [
        EventItemResponse(
            id=e.id,
            session_id=str(e.session_id),
            event_type=e.event_type,
            agent_name=e.agent_name,
            payload=e.payload,
            created_at=e.created_at,
        )
        for e in events
    ]

    next_cursor = items[-1].id if len(items) == limit else None

    return EventsPaginationResponse(
        items=items,
        next_cursor=next_cursor,
        total_returned=len(items),
    )
