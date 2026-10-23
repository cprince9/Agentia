"""001_initial: Initial database migration for MASDS

Creates core entities:
- sessions
- agent_runs
- artifacts
- events
- agent_messages

Revision ID: 001_initial
Revises: None
Create Date: 2026-10-16 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. sessions table
    # -------------------------------------------------------------------------
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('requirement', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='created'),
        sa.Column('current_agent', sa.String(length=50), nullable=True),
        sa.Column('iteration', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_iterations', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_sessions_status', 'sessions', ['status'], unique=False)
    op.create_index('ix_sessions_created_at', 'sessions', ['created_at'], unique=False)

    # -------------------------------------------------------------------------
    # 2. agent_runs table
    # -------------------------------------------------------------------------
    op.create_table(
        'agent_runs',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('session_id', sa.String(length=36), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_name', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('inputs', sa.JSON(), nullable=True),
        sa.Column('outputs', sa.JSON(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duration_seconds', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_agent_runs_session_id', 'agent_runs', ['session_id'], unique=False)
    op.create_index('ix_agent_runs_agent_name', 'agent_runs', ['agent_name'], unique=False)
    op.create_index('ix_agent_runs_status', 'agent_runs', ['status'], unique=False)

    # -------------------------------------------------------------------------
    # 3. artifacts table
    # -------------------------------------------------------------------------
    op.create_table(
        'artifacts',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('session_id', sa.String(length=36), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_run_id', sa.String(length=36), sa.ForeignKey('agent_runs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('artifact_type', sa.String(length=50), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_artifacts_session_id', 'artifacts', ['session_id'], unique=False)
    op.create_index('ix_artifacts_artifact_type', 'artifacts', ['artifact_type'], unique=False)

    # -------------------------------------------------------------------------
    # 4. events table
    # -------------------------------------------------------------------------
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('session_id', sa.String(length=36), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('sender', sa.String(length=50), nullable=False),
        sa.Column('recipient', sa.String(length=50), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_events_session_id', 'events', ['session_id'], unique=False)
    op.create_index('ix_events_event_type', 'events', ['event_type'], unique=False)
    op.create_index('ix_events_created_at', 'events', ['created_at'], unique=False)

    # -------------------------------------------------------------------------
    # 5. agent_messages table
    # -------------------------------------------------------------------------
    op.create_table(
        'agent_messages',
        sa.Column('id', sa.String(length=36), primary_key=True, nullable=False),
        sa.Column('session_id', sa.String(length=36), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_agent', sa.String(length=50), nullable=False),
        sa.Column('receiver_agent', sa.String(length=50), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_agent_messages_session_id', 'agent_messages', ['session_id'], unique=False)
    op.create_index('ix_agent_messages_sender_agent', 'agent_messages', ['sender_agent'], unique=False)
    op.create_index('ix_agent_messages_created_at', 'agent_messages', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop in exact reverse order to satisfy foreign key constraints
    op.drop_index('ix_agent_messages_created_at', table_name='agent_messages')
    op.drop_index('ix_agent_messages_sender_agent', table_name='agent_messages')
    op.drop_index('ix_agent_messages_session_id', table_name='agent_messages')
    op.drop_table('agent_messages')

    op.drop_index('ix_events_created_at', table_name='events')
    op.drop_index('ix_events_event_type', table_name='events')
    op.drop_index('ix_events_session_id', table_name='events')
    op.drop_table('events')

    op.drop_index('ix_artifacts_artifact_type', table_name='artifacts')
    op.drop_index('ix_artifacts_session_id', table_name='artifacts')
    op.drop_table('artifacts')

    op.drop_index('ix_agent_runs_status', table_name='agent_runs')
    op.drop_index('ix_agent_runs_agent_name', table_name='agent_runs')
    op.drop_index('ix_agent_runs_session_id', table_name='agent_runs')
    op.drop_table('agent_runs')

    op.drop_index('ix_sessions_created_at', table_name='sessions')
    op.drop_index('ix_sessions_status', table_name='sessions')
    op.drop_table('sessions')
