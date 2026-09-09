"""add application tracker (companies, tracks, documents, applications, history) + users.is_guest

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-09 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "d4e5f6a7b8c9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None

STATUSES = (
    "discovered", "reviewing", "applied", "doc_passed", "coding_test", "assignment",
    "interview", "offer", "rejected", "withdrawn", "no_response", "not_applied",
)
END_STAGES = ("document", "coding_test", "written_test", "assignment", "interview", "final")
EMPLOYMENT = ("full_time", "contract", "intern_conversion", "intern_experience", "bootcamp")
HIRING = ("open_recruitment", "rolling", "always_open")


def _in(col: str, values: tuple[str, ...]) -> str:
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


def upgrade() -> None:
    # 게스트도 진짜 users 행으로 — anonymous 공유 유저 제거의 전제
    op.add_column("users", sa.Column("is_guest", sa.Boolean(), server_default=sa.false(), nullable=False))

    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("size", sa.String(50), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("memo", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_companies_user_name"),
    )
    op.create_index("ix_companies_user_id", "companies", ["user_id"])

    op.create_table(
        "tracks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("color", sa.String(7), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_tracks_user_name"),
    )
    op.create_index("ix_tracks_user_id", "tracks", ["user_id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("doc_type", sa.String(20), server_default="resume", nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "title", name="uq_documents_user_title"),
        sa.CheckConstraint(_in("doc_type", ("resume", "cover_letter", "portfolio")), name="ck_documents_doc_type"),
    )
    op.create_index("ix_documents_user_id", "documents", ["user_id"])

    op.create_table(
        "applications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("track_id", sa.Uuid(), nullable=True),
        sa.Column("resume_document_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("position", sa.String(200), nullable=False),
        sa.Column("posting_url", sa.String(1000), nullable=True),
        sa.Column("status", sa.String(30), server_default="discovered", nullable=False),
        sa.Column("end_stage", sa.String(30), nullable=True),
        sa.Column("employment_type", sa.String(30), nullable=True),
        sa.Column("hiring_type", sa.String(30), nullable=True),
        sa.Column("discovered_at", sa.Date(), nullable=True),
        sa.Column("applied_at", sa.Date(), nullable=True),
        sa.Column("deadline_at", sa.Date(), nullable=True),
        sa.Column("next_event_at", sa.DateTime(), nullable=True),
        sa.Column("next_action", sa.String(500), nullable=True),
        sa.Column("retrospective", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resume_document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "company_id", "title", name="uq_applications_user_company_title"),
        sa.CheckConstraint(_in("status", STATUSES), name="ck_applications_status"),
        sa.CheckConstraint("end_stage IS NULL OR status IN ('rejected', 'withdrawn')", name="ck_app_end_stage_only_when_closed"),
        sa.CheckConstraint(f"end_stage IS NULL OR {_in('end_stage', END_STAGES)}", name="ck_applications_end_stage"),
        sa.CheckConstraint(f"employment_type IS NULL OR {_in('employment_type', EMPLOYMENT)}", name="ck_applications_employment_type"),
        sa.CheckConstraint(f"hiring_type IS NULL OR {_in('hiring_type', HIRING)}", name="ck_applications_hiring_type"),
    )
    op.create_index("ix_applications_user_id", "applications", ["user_id"])
    op.create_index("ix_applications_user_status", "applications", ["user_id", "status"])
    op.create_index("ix_applications_user_deadline", "applications", ["user_id", "deadline_at"])
    op.create_index("ix_applications_user_applied", "applications", ["user_id", "applied_at"])

    op.create_table(
        "application_status_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("from_status", sa.String(30), nullable=True),
        sa.Column("to_status", sa.String(30), nullable=False),
        sa.Column("changed_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("source", sa.String(20), server_default="user", nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(_in("source", ("user", "agent", "import")), name="ck_app_history_source"),
    )
    op.create_index("ix_app_history_app_changed", "application_status_history", ["application_id", "changed_at"])


def downgrade() -> None:
    op.drop_table("application_status_history")
    op.drop_table("applications")
    op.drop_table("documents")
    op.drop_table("tracks")
    op.drop_table("companies")
    op.drop_column("users", "is_guest")
