"""Initial headless schema; deliberately has no legacy migration path.

Revision ID: 029_headless_01
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

from alembic import op

revision = "029_headless_01"
down_revision = None
branch_labels = None
depends_on = None


def identity():
    return sa.Column("id", pg.UUID(as_uuid=True), primary_key=True)


def timestamps():
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade():
    op.create_table(
        "maos_instance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product", sa.String(40), nullable=False),
    )
    op.execute("INSERT INTO maos_instance (id, product) VALUES (1, 'headless-1')")
    op.create_table(
        "worker_presence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "users",
        identity(),
        *timestamps(),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table(
        "roles",
        identity(),
        *timestamps(),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.String(500)),
    )
    op.create_index("ix_roles_name", "roles", ["name"])
    op.create_table(
        "user_roles",
        sa.Column(
            "user_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "role_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_table(
        "refresh_sessions",
        identity(),
        sa.Column(
            "user_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])
    op.create_table(
        "audit_logs",
        identity(),
        *timestamps(),
        sa.Column("workflow_id", pg.UUID(as_uuid=True)),
        sa.Column("actor_type", sa.String(100)),
        sa.Column("actor_id", pg.UUID(as_uuid=True)),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", pg.UUID(as_uuid=True)),
        sa.Column("payload", pg.JSONB(), nullable=False),
    )
    op.create_table(
        "runs",
        identity(),
        *timestamps(),
        sa.Column("workflow_id", sa.String(100), nullable=False),
        sa.Column("workflow_version", sa.String(40), nullable=False),
        sa.Column("definition_hash", sa.String(64), nullable=False),
        sa.Column("definition_snapshot", pg.JSONB(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column(
            "created_by_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("input", pg.JSONB(), nullable=False),
        sa.Column("context", pg.JSONB(), nullable=False),
        sa.Column("outputs", pg.JSONB(), nullable=False),
        sa.Column("final_output", pg.JSONB()),
        sa.Column("provider_profile", pg.JSONB(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("event_sequence", sa.Integer(), nullable=False),
        sa.Column("current_node", sa.String(100)),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("owner", sa.String(100)),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True)),
        sa.Column("call_count", sa.Integer(), nullable=False),
        sa.Column("error", pg.JSONB()),
    )
    op.create_index("ix_runs_workflow_id", "runs", ["workflow_id"])
    op.create_index("ix_runs_status", "runs", ["status"])
    op.create_table(
        "jobs",
        identity(),
        *timestamps(),
        sa.Column(
            "run_id",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("runs.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("status", sa.String(20), nullable=False),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_table(
        "node_executions",
        identity(),
        *timestamps(),
        sa.Column(
            "run_id", pg.UUID(as_uuid=True), sa.ForeignKey("runs.id"), nullable=False
        ),
        sa.Column("node_id", sa.String(100), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("generation", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("output", pg.JSONB()),
        sa.Column("execution_metadata", pg.JSONB(), nullable=False),
        sa.Column("error", pg.JSONB()),
        sa.UniqueConstraint("run_id", "node_id", "attempt"),
    )
    op.create_index("ix_node_executions_run_id", "node_executions", ["run_id"])
    op.create_table(
        "approvals",
        identity(),
        *timestamps(),
        sa.Column(
            "run_id", pg.UUID(as_uuid=True), sa.ForeignKey("runs.id"), nullable=False
        ),
        sa.Column("node_id", sa.String(100), nullable=False),
        sa.Column("workflow_version", sa.String(40), nullable=False),
        sa.Column("definition_hash", sa.String(64), nullable=False),
        sa.Column("content_revision", sa.Integer(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("content", pg.JSONB(), nullable=False),
        sa.Column("decision", sa.String(20)),
        sa.Column("actor_id", pg.UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("decided_at", sa.DateTime(timezone=True)),
        sa.Column("comment", sa.String(2000)),
        sa.UniqueConstraint("run_id", "node_id"),
    )
    op.create_index("ix_approvals_run_id", "approvals", ["run_id"])
    op.create_table(
        "run_events",
        identity(),
        *timestamps(),
        sa.Column(
            "run_id", pg.UUID(as_uuid=True), sa.ForeignKey("runs.id"), nullable=False
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("actor_id", pg.UUID(as_uuid=True)),
        sa.Column("node_id", sa.String(100)),
        sa.Column("payload", pg.JSONB(), nullable=False),
        sa.UniqueConstraint("run_id", "sequence"),
    )
    op.create_index("ix_run_events_run_id", "run_events", ["run_id"])
    op.create_table(
        "idempotency_records",
        identity(),
        *timestamps(),
        sa.Column(
            "principal",
            pg.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("family", sa.String(20), nullable=False),
        sa.Column("key", sa.String(200), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column(
            "run_id", pg.UUID(as_uuid=True), sa.ForeignKey("runs.id"), nullable=False
        ),
        sa.UniqueConstraint("principal", "family", "key"),
    )


def downgrade():
    raise RuntimeError(
        "Destructive downgrade is unsupported; restore a verified backup "
        "into a separate database"
    )
