"""SQLAlchemy ORM models for MASDS database entities."""

import uuid
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    Float,
    DateTime,
    JSON,
    ForeignKey,
    func,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=True)
    requirement = Column(Text, nullable=False)
    status = Column(String(50), default="created", nullable=False, index=True)
    current_agent = Column(String(50), nullable=True)
    iteration = Column(Integer, default=0, nullable=False)
    max_iterations = Column(Integer, default=5, nullable=False)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    runs = relationship("AgentRun", back_populates="session", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="session", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="session", cascade="all, delete-orphan")
    messages = relationship("AgentMessage", back_populates="session", cascade="all, delete-orphan")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False, index=True)
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    token_count = Column(Integer, default=0, nullable=False)
    duration_seconds = Column(Float, default=0.0, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("Session", back_populates="runs")
    artifacts = relationship("Artifact", back_populates="agent_run")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    artifact_type = Column(String(50), nullable=False, index=True)
    file_path = Column(String(512), nullable=True)
    content = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    session = relationship("Session", back_populates="artifacts")
    agent_run = relationship("AgentRun", back_populates="artifacts")


class Event(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    sender = Column(String(50), nullable=False)
    recipient = Column(String(50), nullable=True)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    session = relationship("Session", back_populates="events")


class AgentMessage(Base):
    __tablename__ = "agent_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_agent = Column(String(50), nullable=False, index=True)
    receiver_agent = Column(String(50), nullable=False)
    message_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationships
    session = relationship("Session", back_populates="messages")
