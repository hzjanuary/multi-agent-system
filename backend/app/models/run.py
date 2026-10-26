"""PostgreSQL state authority for runs, work ownership and committed history."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import RunStatus


class Instance(Base):
    __tablename__ = "maos_instance"
    id: Mapped[int] = mapped_column(primary_key=True)
    product: Mapped[str] = mapped_column(String(40))


class WorkerPresence(Base):
    """Singleton liveness signal, independent of correctness-critical run leases."""

    __tablename__ = "worker_presence"
    id: Mapped[int] = mapped_column(primary_key=True)
    heartbeat_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Run(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "runs"
    workflow_id: Mapped[str] = mapped_column(String(100), index=True)
    workflow_version: Mapped[str] = mapped_column(String(40))
    definition_hash: Mapped[str] = mapped_column(String(64))
    definition_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    schema_version: Mapped[int] = mapped_column(default=1)
    created_by_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    input: Mapped[dict[str, Any]] = mapped_column(JSONB)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    final_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    provider_profile: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(
        String(32), default=RunStatus.CREATED, index=True
    )
    revision: Mapped[int] = mapped_column(Integer, default=1)
    event_sequence: Mapped[int] = mapped_column(Integer, default=0)
    current_node: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    generation: Mapped[int] = mapped_column(Integer, default=0)
    owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    call_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class Job(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "jobs"
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="QUEUED", index=True)


class NodeExecution(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "node_executions"
    __table_args__ = (UniqueConstraint("run_id", "node_id", "attempt"),)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"), index=True)
    node_id: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(20))
    attempt: Mapped[int] = mapped_column(Integer)
    generation: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20))
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    execution_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    error: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)


class Approval(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "approvals"
    __table_args__ = (UniqueConstraint("run_id", "node_id"),)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"), index=True)
    node_id: Mapped[str] = mapped_column(String(100))
    workflow_version: Mapped[str] = mapped_column(String(40))
    definition_hash: Mapped[str] = mapped_column(String(64))
    content_revision: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    decision: Mapped[str | None] = mapped_column(String(20), nullable=True)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    comment: Mapped[str | None] = mapped_column(String(2000), nullable=True)


class RunEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "run_events"
    __table_args__ = (UniqueConstraint("run_id", "sequence"),)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"), index=True)
    sequence: Mapped[int] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(80))
    actor_id: Mapped[UUID | None] = mapped_column(nullable=True)
    node_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class Idempotency(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("principal", "family", "key"),)
    principal: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    family: Mapped[str] = mapped_column(String(20))
    key: Mapped[str] = mapped_column(String(200))
    fingerprint: Mapped[str] = mapped_column(String(64))
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"))
