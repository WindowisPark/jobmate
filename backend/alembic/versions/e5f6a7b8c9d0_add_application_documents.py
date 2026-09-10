"""지원 ↔ 제출물 다대다 (자소서 배제 전형 대응) + 제출물 종류 확장

한 지원에 이력서 하나만 걸리던 구조를 조인 테이블로 바꾼다.
자소서를 빼고 이력서·포트폴리오·경험기술서를 함께 받는 전형이 늘면서
'지원 1건 = 이력서 1개' 가정이 깨졌고, 그 가정 위에서는
"포트폴리오 v2 를 붙인 지원의 서류 통과율" 을 물을 수 없다.

기존 applications.resume_document_id 값은 조인 테이블로 옮긴 뒤 컬럼을 지운다.
데이터가 쌓이기 전에 처리해 이전 비용을 없앤다.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-10 00:00:00.000000
"""

import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None

OLD_DOC_TYPES = ("resume", "cover_letter", "portfolio")
NEW_DOC_TYPES = ("resume", "cover_letter", "portfolio", "experience", "other")


def _in(col: str, values: tuple[str, ...]) -> str:
    return f"{col} IN ({', '.join(repr(v) for v in values)})"


def upgrade() -> None:
    op.create_table(
        "application_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("application_id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("attached_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("application_id", "document_id", name="uq_app_documents_app_doc"),
    )
    op.create_index("ix_application_documents_application_id", "application_documents", ["application_id"])
    op.create_index("ix_app_documents_document", "application_documents", ["document_id"])

    # 기존 단일 이력서 연결을 조인 테이블로 이전
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, resume_document_id FROM applications WHERE resume_document_id IS NOT NULL"
        )
    ).fetchall()
    if rows:
        now = datetime.utcnow()
        conn.execute(
            sa.text(
                "INSERT INTO application_documents (id, application_id, document_id, attached_at)"
                " VALUES (:id, :app_id, :doc_id, :at)"
            ),
            [
                {"id": uuid.uuid4(), "app_id": r[0], "doc_id": r[1], "at": now}
                for r in rows
            ],
        )

    op.drop_column("applications", "resume_document_id")

    # 제출물 종류에 경험기술서·기타 추가
    op.drop_constraint("ck_documents_doc_type", "documents", type_="check")
    op.create_check_constraint("ck_documents_doc_type", "documents", _in("doc_type", NEW_DOC_TYPES))


def downgrade() -> None:
    op.add_column("applications", sa.Column("resume_document_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_applications_resume_document_id",
        "applications",
        "documents",
        ["resume_document_id"],
        ["id"],
        ondelete="SET NULL",
    )
    # 지원마다 가장 먼저 붙인 제출물 하나만 되돌린다 — 나머지 연결은 사라진다
    op.execute(
        "UPDATE applications a SET resume_document_id = ("
        " SELECT ad.document_id FROM application_documents ad"
        " WHERE ad.application_id = a.id ORDER BY ad.attached_at LIMIT 1)"
    )

    op.drop_index("ix_app_documents_document", table_name="application_documents")
    op.drop_index("ix_application_documents_application_id", table_name="application_documents")
    op.drop_table("application_documents")

    # 되돌린 CHECK 를 위반할 값을 먼저 정리
    op.execute("UPDATE documents SET doc_type = 'resume' WHERE doc_type IN ('experience', 'other')")
    op.drop_constraint("ck_documents_doc_type", "documents", type_="check")
    op.create_check_constraint("ck_documents_doc_type", "documents", _in("doc_type", OLD_DOC_TYPES))
