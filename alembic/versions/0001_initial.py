"""Initial schema for datasets, events, jobs, and import drafts."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("generator_seed", sa.Integer(), nullable=True),
        sa.Column("generator_cases", sa.Integer(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("eligible_event_count", sa.Integer(), nullable=False),
        sa.Column("case_count", sa.Integer(), nullable=False),
        sa.Column("conformance_json", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=False),
        sa.Column("source_row", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.String(length=200), nullable=True),
        sa.Column("activity", sa.String(length=200), nullable=True),
        sa.Column("timestamp_utc", sa.DateTime(), nullable=True),
        sa.Column("raw_timestamp", sa.String(length=80), nullable=True),
        sa.Column("resource", sa.String(length=200), nullable=True),
        sa.Column("role", sa.String(length=200), nullable=True),
        sa.Column("channel", sa.String(length=200), nullable=True),
        sa.Column("outcome", sa.String(length=200), nullable=True),
        sa.Column("cost", sa.Float(), nullable=True),
        sa.Column("job_family", sa.String(length=200), nullable=True),
        sa.Column("exclusion_reason", sa.String(length=64), nullable=True),
        sa.Column("warning", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dataset_id", "source_row", name="uq_event_dataset_row"),
    )
    op.create_index("ix_events_dataset_id", "events", ["dataset_id"])
    op.create_index("ix_events_dataset_case", "events", ["dataset_id", "case_id"])
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("dataset_id", sa.String(length=36), nullable=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "drafts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("csv_text", sa.Text(), nullable=False),
        sa.Column("synthetic", sa.Boolean(), nullable=False),
        sa.Column("timezone_suggestion", sa.String(length=64), nullable=False),
        sa.Column("generator_seed", sa.Integer(), nullable=True),
        sa.Column("generator_cases", sa.Integer(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("drafts")
    op.drop_table("jobs")
    op.drop_index("ix_events_dataset_case", table_name="events")
    op.drop_index("ix_events_dataset_id", table_name="events")
    op.drop_table("events")
    op.drop_table("datasets")
