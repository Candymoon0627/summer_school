"""add teacher submissions

Revision ID: 0002_submissions
Revises: 0001_initial_schema
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_submissions"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "submissions" not in existing_tables:
        op.create_table(
            "submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("teacher_id", sa.Uuid(), nullable=True),
        sa.Column("school_id", sa.Uuid(), nullable=True),
        sa.Column("region_id", sa.Uuid(), nullable=True),
        sa.Column("knowledge_item_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("current_review_stage", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_message_id", sa.String(length=255), nullable=True),
        sa.Column("raw_input", sa.Text(), nullable=True),
        sa.Column("visibility_scope", sa.String(length=64), nullable=False),
        sa.Column("knowledge_type", sa.String(length=64), nullable=False),
        sa.Column("subject", sa.String(length=64), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("target_grade", sa.Integer(), nullable=True),
        sa.Column("grade_min", sa.Integer(), nullable=False),
        sa.Column("grade_max", sa.Integer(), nullable=False),
        sa.Column("content_th", sa.Text(), nullable=True),
        sa.Column("content_ms", sa.Text(), nullable=True),
        sa.Column("content_en", sa.Text(), nullable=True),
        sa.Column("local_context", sa.Text(), nullable=True),
        sa.Column("classroom_use", sa.Text(), nullable=True),
        sa.Column("safety_notes", sa.Text(), nullable=True),
        sa.Column("source_note", sa.Text(), nullable=True),
        sa.Column("sensitive_status", sa.String(length=64), nullable=False),
        sa.Column("copyright_status", sa.String(length=64), nullable=False),
        sa.Column("duplicate_status", sa.String(length=64), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("second_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(["knowledge_item_id"], ["knowledge_items.id"]),
            sa.ForeignKeyConstraint(["region_id"], ["regions.id"]),
            sa.ForeignKeyConstraint(["school_id"], ["schools.id"]),
            sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_submissions_duplicate_status"), "submissions", ["duplicate_status"])
        op.create_index(op.f("ix_submissions_knowledge_item_id"), "submissions", ["knowledge_item_id"])
        op.create_index(op.f("ix_submissions_knowledge_type"), "submissions", ["knowledge_type"])
        op.create_index(op.f("ix_submissions_region_id"), "submissions", ["region_id"])
        op.create_index(op.f("ix_submissions_school_id"), "submissions", ["school_id"])
        op.create_index(op.f("ix_submissions_sensitive_status"), "submissions", ["sensitive_status"])
        op.create_index(op.f("ix_submissions_source_message_id"), "submissions", ["source_message_id"])
        op.create_index(op.f("ix_submissions_source_type"), "submissions", ["source_type"])
        op.create_index(op.f("ix_submissions_status"), "submissions", ["status"])
        op.create_index(op.f("ix_submissions_subject"), "submissions", ["subject"])
        op.create_index(op.f("ix_submissions_target_grade"), "submissions", ["target_grade"])
        op.create_index(op.f("ix_submissions_teacher_id"), "submissions", ["teacher_id"])
        op.create_index(op.f("ix_submissions_topic"), "submissions", ["topic"])
        op.create_index(op.f("ix_submissions_visibility_scope"), "submissions", ["visibility_scope"])

    if "submission_reviews" not in existing_tables:
        op.create_table(
            "submission_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("stage", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("reviewer_username", sa.String(length=255), nullable=True),
        sa.Column("reviewer_role", sa.String(length=64), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("before_status", sa.String(length=64), nullable=True),
        sa.Column("after_status", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_submission_reviews_action"), "submission_reviews", ["action"])
        op.create_index(op.f("ix_submission_reviews_submission_id"), "submission_reviews", ["submission_id"])


def downgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())
    if "submission_reviews" in existing_tables:
        op.drop_index(op.f("ix_submission_reviews_submission_id"), table_name="submission_reviews")
        op.drop_index(op.f("ix_submission_reviews_action"), table_name="submission_reviews")
        op.drop_table("submission_reviews")
    if "submissions" in existing_tables:
        op.drop_index(op.f("ix_submissions_visibility_scope"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_topic"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_teacher_id"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_target_grade"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_subject"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_status"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_source_type"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_source_message_id"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_sensitive_status"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_school_id"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_region_id"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_knowledge_type"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_knowledge_item_id"), table_name="submissions")
        op.drop_index(op.f("ix_submissions_duplicate_status"), table_name="submissions")
        op.drop_table("submissions")
