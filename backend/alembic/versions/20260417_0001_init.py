"""init users, annotation_runs, llm_config_presets

Revision ID: 20260417_0001
Revises:
Create Date: 2026-04-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "20260417_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("github_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("github_login", sa.String(), nullable=False),
        sa.Column("name", sa.String()),
        sa.Column("email", sa.String()),
        sa.Column("avatar_url", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "annotation_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.String(), nullable=False, unique=True),
        sa.Column("dataset_id", sa.String(), nullable=False),
        sa.Column("dataset_filename", sa.String(), nullable=False),
        sa.Column("total_sessions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_sessions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("llm_config_snapshot", JSONB(), nullable=False),
        sa.Column("flagged_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("resolved_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_runs_user_created", "annotation_runs", ["user_id", "created_at"])

    op.create_table(
        "llm_config_presets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String()),
        sa.Column("config_json", JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "name", name="uq_presets_user_name"),
    )
    op.create_index("ix_presets_user_updated", "llm_config_presets", ["user_id", "updated_at"])


def downgrade() -> None:
    op.drop_index("ix_presets_user_updated", table_name="llm_config_presets")
    op.drop_table("llm_config_presets")
    op.drop_index("ix_runs_user_created", table_name="annotation_runs")
    op.drop_table("annotation_runs")
    op.drop_table("users")
