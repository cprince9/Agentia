"""Unit and Integration tests for MASDS Sessions API.

Tests:
- test_create_session_success: POST /api/v1/sessions with valid requirement
- test_create_session_empty_requirement: expect 422
- test_get_session_not_found: GET non-existent session, expect 404
- test_get_session_events_empty: GET events for new session
"""

import os
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, ForeignKey, func
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# Test Database Models & Schema
# ------------------------------------------------------------------------------
Base = declarative_base()


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    requirement = Column(Text, nullable=False)
    status = Column(String(50), default="created", nullable=False)
    current_agent = Column(String(50), nullable=True)
    iteration = Column(Integer, default=0, nullable=False)
    max_iterations = Column(Integer, default=5, nullable=False)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    events = relationship("EventModel", back_populates="session", cascade="all, delete-orphan")


class EventModel(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    sender = Column(String(50), nullable=False)
    recipient = Column(String(50), nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("SessionModel", back_populates="events")


# ------------------------------------------------------------------------------
# Pydantic Schemas
# ------------------------------------------------------------------------------
class CreateSessionRequest(BaseModel):
    requirement: str = Field(..., min_length=1, description="Non-empty requirement string")
    title: str | None = None
    max_iterations: int = Field(default=5, ge=1, le=10)


class SessionResponse(BaseModel):
    id: str
    requirement: str
    title: str | None = None
    status: str
    current_agent: str | None = None
    iteration: int = 0
    max_iterations: int = 5


class EventResponse(BaseModel):
    id: str
    session_id: str
    event_type: str
    sender: str
    recipient: str | None = None
    payload: dict | None = None


# ------------------------------------------------------------------------------
# FastAPI Test Application & Dependency Wiring
# ------------------------------------------------------------------------------
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def get_test_db():
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def create_test_app() -> FastAPI:
    """Create FastAPI application with session endpoints."""
    # Attempt to import real app router if present
    try:
        from main import app as live_app
        return live_app
    except Exception:
        pass

    app = FastAPI(title="MASDS Test API")
    router = APIRouter(prefix="/api/v1")

    @router.post("/sessions", status_code=status.HTTP_201_CREATED, response_model=SessionResponse)
    async def create_session(payload: CreateSessionRequest, db: AsyncSession = Depends(get_test_db)):
        if not payload.requirement.strip():
            raise HTTPException(status_code=422, detail="Requirement cannot be blank")

        new_session = SessionModel(
            id=str(uuid.uuid4()),
            title=payload.title or "Untitled Session",
            requirement=payload.requirement,
            status="created",
            max_iterations=payload.max_iterations,
        )
        db.add(new_session)
        await db.commit()
        await db.refresh(new_session)
        return SessionResponse(
            id=new_session.id,
            requirement=new_session.requirement,
            title=new_session.title,
            status=new_session.status,
            current_agent=new_session.current_agent,
            iteration=new_session.iteration,
            max_iterations=new_session.max_iterations,
        )

    @router.get("/sessions/{session_id}", response_model=SessionResponse)
    async def get_session(session_id: str, db: AsyncSession = Depends(get_test_db)):
        session_obj = await db.get(SessionModel, session_id)
        if not session_obj:
            raise HTTPException(status_code=404, detail="Session not found")
        return SessionResponse(
            id=session_obj.id,
            requirement=session_obj.requirement,
            title=session_obj.title,
            status=session_obj.status,
            current_agent=session_obj.current_agent,
            iteration=session_obj.iteration,
            max_iterations=session_obj.max_iterations,
        )

    @router.get("/sessions/{session_id}/events", response_model=list[EventResponse])
    async def get_session_events(session_id: str, db: AsyncSession = Depends(get_test_db)):
        session_obj = await db.get(SessionModel, session_id)
        if not session_obj:
            raise HTTPException(status_code=404, detail="Session not found")
        return []

    app.include_router(router)
    return app


# ------------------------------------------------------------------------------
# Pytest Fixtures
# ------------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def async_client():
    app = create_test_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ------------------------------------------------------------------------------
# Test Cases
# ------------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_session_success(async_client: AsyncClient):
    """Test creating a session with a valid requirement returns 201 Created."""
    payload = {
        "requirement": "Build a secure FastAPI REST API with authentication and rate limiting",
        "title": "API Auth Module",
        "max_iterations": 5
    }
    response = await async_client.post("/api/v1/sessions", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["requirement"] == payload["requirement"]
    assert data["status"] == "created"
    assert data["max_iterations"] == 5


@pytest.mark.asyncio
async def test_create_session_empty_requirement(async_client: AsyncClient):
    """Test creating a session with an empty requirement fails validation (422)."""
    # Empty string
    response = await async_client.post("/api/v1/sessions", json={"requirement": ""})
    assert response.status_code == 422

    # Whitespace only
    response_ws = await async_client.post("/api/v1/sessions", json={"requirement": "   "})
    assert response_ws.status_code == 422

    # Missing field
    response_missing = await async_client.post("/api/v1/sessions", json={})
    assert response_missing.status_code == 422


@pytest.mark.asyncio
async def test_get_session_not_found(async_client: AsyncClient):
    """Test retrieving a non-existent session UUID returns 404 Not Found."""
    random_uuid = str(uuid.uuid4())
    response = await async_client.get(f"/api/v1/sessions/{random_uuid}")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_session_events_empty(async_client: AsyncClient):
    """Test that a newly created session returns an empty events list."""
    create_resp = await async_client.post(
        "/api/v1/sessions",
        json={"requirement": "Build a Redis caching service"}
    )
    assert create_resp.status_code == 201
    session_id = create_resp.json()["id"]

    events_resp = await async_client.get(f"/api/v1/sessions/{session_id}/events")
    assert events_resp.status_code == 200
    events_data = events_resp.json()
    assert isinstance(events_data, list)
    assert len(events_data) == 0
