import uuid
from datetime import datetime, timezone
from typing import List, Optional, Any, Union
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Session, AgentRun, Artifact, Event, AgentMessage


def _ensure_uuid(val: Union[str, uuid.UUID]) -> uuid.UUID:
    if isinstance(val, str):
        return uuid.UUID(val)
    return val


async def create_session(
    db: AsyncSession,
    requirement: str,
    user_id: Optional[Union[str, uuid.UUID]] = None,
) -> Session:
    uid = _ensure_uuid(user_id) if user_id else None
    session = Session(
        requirement=requirement,
        user_id=uid,
        status="pending",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(
    db: AsyncSession,
    session_id: Union[str, uuid.UUID],
    load_relations: bool = False,
) -> Optional[Session]:
    sid = _ensure_uuid(session_id)
    if load_relations:
        stmt = (
            select(Session)
            .where(Session.id == sid)
            .options(
                selectinload(Session.agent_runs),
                selectinload(Session.artifacts),
                selectinload(Session.events),
                selectinload(Session.agent_messages),
            )
        )
    else:
        stmt = select(Session).where(Session.id == sid)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_session_status(
    db: AsyncSession,
    session_id: Union[str, uuid.UUID],
    status: str,
    **kwargs: Any,
) -> Optional[Session]:
    sid = _ensure_uuid(session_id)
    session = await get_session(db, sid)
    if not session:
        return None

    session.status = status
    session.updated_at = datetime.now(timezone.utc)

    if status in ("completed", "failed") and "completed_at" not in kwargs:
        session.completed_at = datetime.now(timezone.utc)

    for key, val in kwargs.items():
        if hasattr(session, key):
            setattr(session, key, val)

    await db.commit()
    await db.refresh(session)
    return session


async def create_agent_run(
    db: AsyncSession,
    session_id: Union[str, uuid.UUID],
    agent_name: str,
    llm_model: Optional[str] = None,
) -> AgentRun:
    sid = _ensure_uuid(session_id)
    run = AgentRun(
        session_id=sid,
        agent_name=agent_name,
        status="running",
        started_at=datetime.now(timezone.utc),
        llm_model=llm_model,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def update_agent_run(
    db: AsyncSession,
    run_id: Union[str, uuid.UUID],
    **kwargs: Any,
) -> Optional[AgentRun]:
    rid = _ensure_uuid(run_id)
    stmt = select(AgentRun).where(AgentRun.id == rid)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        return None

    for key, val in kwargs.items():
        if hasattr(run, key):
            setattr(run, key, val)

    if "status" in kwargs and kwargs["status"] in ("completed", "failed") and "ended_at" not in kwargs:
        run.ended_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(run)
    return run


async def get_agent_runs(
    db: AsyncSession,
    session_id: Union[str, uuid.UUID],
) -> List[AgentRun]:
    sid = _ensure_uuid(session_id)
    stmt = (
        select(AgentRun)
        .where(AgentRun.session_id == sid)
        .order_by(AgentRun.started_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_artifact(
    db: AsyncSession,
    session_id: Union[str, uuid.UUID],
    file_path: str,
    file_type: str,
    s3_key: Optional[str] = None,
    size_bytes: Optional[int] = None,
) -> Artifact:
    sid = _ensure_uuid(session_id)
    artifact = Artifact(
        session_id=sid,
        file_path=file_path,
        file_type=file_type,
        s3_key=s3_key,
        size_bytes=size_bytes,
        created_at=datetime.now(timezone.utc),
    )
    db.add(artifact)
    await db.commit()
    await db.refresh(artifact)
    return artifact


async def get_artifacts(
    db: AsyncSession,
    session_id: Union[str, uuid.UUID],
) -> List[Artifact]:
    sid = _ensure_uuid(session_id)
    stmt = (
        select(Artifact)
        .where(Artifact.session_id == sid)
        .order_by(Artifact.created_at)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_event(
    db: AsyncSession,
    session_id: Union[str, uuid.UUID],
    event_type: str,
    agent_name: Optional[str] = None,
    payload: Optional[dict] = None,
) -> Event:
    sid = _ensure_uuid(session_id)
    event = Event(
        session_id=sid,
        event_type=event_type,
        agent_name=agent_name,
        payload=payload,
        created_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def get_events(
    db: AsyncSession,
    session_id: Union[str, uuid.UUID],
    cursor: int = 0,
    limit: int = 50,
) -> List[Event]:
    sid = _ensure_uuid(session_id)
    stmt = (
        select(Event)
        .where(Event.session_id == sid, Event.id > cursor)
        .order_by(Event.id.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create_agent_message(
    db: AsyncSession,
    session_id: Union[str, uuid.UUID],
    from_agent: str,
    to_agent: str,
    message: str,
) -> AgentMessage:
    sid = _ensure_uuid(session_id)
    agent_msg = AgentMessage(
        session_id=sid,
        from_agent=from_agent,
        to_agent=to_agent,
        message=message,
        created_at=datetime.now(timezone.utc),
    )
    db.add(agent_msg)
    await db.commit()
    await db.refresh(agent_msg)
    return agent_msg
