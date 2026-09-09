"""지원 추적(트래커) 도메인.

companies · tracks · documents · applications · application_status_history.

오너의 노션 "📝 지원" DB 스키마를 그대로 포팅했다. DB에는 영문 키(String + CHECK)를 저장하고
한글 라벨은 여기 상수로 관리한다(프런트 types/application.ts 가 미러). ENUM 타입을 쓰지 않는 이유는
상태 추가 시 ALTER TYPE 없이 CHECK 만 갈아끼우면 되기 때문(messages.sender_type 과 같은 패턴).
"""

import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class ApplicationStatus(StrEnum):
    DISCOVERED = "discovered"
    REVIEWING = "reviewing"
    APPLIED = "applied"
    DOC_PASSED = "doc_passed"
    CODING_TEST = "coding_test"
    ASSIGNMENT = "assignment"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    NO_RESPONSE = "no_response"
    NOT_APPLIED = "not_applied"


STATUS_LABELS: dict[str, str] = {
    "discovered": "발견",
    "reviewing": "검토중",
    "applied": "지원완료",
    "doc_passed": "서류통과",
    "coding_test": "코테·필기",
    "assignment": "과제",
    "interview": "면접",
    "offer": "최종합격",
    "rejected": "탈락",
    "withdrawn": "포기",
    "no_response": "무응답",
    "not_applied": "미지원",
}

# 🔥 진행중 보드에 올라가는 상태(노션 뷰 필터와 동일, 순서 = 칸반 컬럼 순서)
ACTIVE_STATUSES: tuple[str, ...] = (
    "discovered",
    "reviewing",
    "applied",
    "doc_passed",
    "coding_test",
    "assignment",
    "interview",
)
# 종료단계(end_stage)를 가질 수 있는 상태
CLOSED_WITH_STAGE: frozenset[str] = frozenset({"rejected", "withdrawn"})


class EndStage(StrEnum):
    DOCUMENT = "document"
    CODING_TEST = "coding_test"
    WRITTEN_TEST = "written_test"
    ASSIGNMENT = "assignment"
    INTERVIEW = "interview"
    FINAL = "final"


END_STAGE_LABELS: dict[str, str] = {
    "document": "서류",
    "coding_test": "코테",
    "written_test": "필기",
    "assignment": "과제",
    "interview": "면접",
    "final": "최종",
}


class EmploymentType(StrEnum):
    FULL_TIME = "full_time"
    CONTRACT = "contract"
    INTERN_CONVERSION = "intern_conversion"
    INTERN_EXPERIENCE = "intern_experience"
    BOOTCAMP = "bootcamp"


EMPLOYMENT_LABELS: dict[str, str] = {
    "full_time": "정규직",
    "contract": "계약직",
    "intern_conversion": "채용연계형 인턴",
    "intern_experience": "체험형 인턴",
    "bootcamp": "부트캠프/교육",
}


class HiringType(StrEnum):
    OPEN_RECRUITMENT = "open_recruitment"
    ROLLING = "rolling"
    ALWAYS_OPEN = "always_open"


HIRING_LABELS: dict[str, str] = {
    "open_recruitment": "공채",
    "rolling": "수시",
    "always_open": "상시",
}

DOC_TYPES: tuple[str, ...] = ("resume", "cover_letter", "portfolio")
HISTORY_SOURCES: tuple[str, ...] = ("user", "agent", "import")


def _in_list(column: str, values: tuple[str, ...] | list[str]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_companies_user_name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100))
    size: Mapped[str | None] = mapped_column(String(50))
    website: Mapped[str | None] = mapped_column(String(500))
    memo: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    applications: Mapped[list["Application"]] = relationship(back_populates="company")


class Track(Base):
    """지원 트랙(백엔드·데이터 등). 노션 '트랙' 관계."""

    __tablename__ = "tracks"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tracks_user_name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str | None] = mapped_column(String(7))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Document(Base):
    """이력서·자소서 버전(📚 건물의 씨앗).

    v1은 제목만 — 노션 '이력서 버전' 관계를 받기 위한 stub.
    """

    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("user_id", "title", name="uq_documents_user_title"),
        CheckConstraint(_in_list("doc_type", DOC_TYPES), name="ck_documents_doc_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    doc_type: Mapped[str] = mapped_column(String(20), nullable=False, default="resume")
    content: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        CheckConstraint(
            _in_list("status", tuple(s.value for s in ApplicationStatus)),
            name="ck_applications_status",
        ),
        CheckConstraint(
            "end_stage IS NULL OR status IN ('rejected', 'withdrawn')",
            name="ck_app_end_stage_only_when_closed",
        ),
        CheckConstraint(
            f"end_stage IS NULL OR {_in_list('end_stage', tuple(s.value for s in EndStage))}",
            name="ck_applications_end_stage",
        ),
        CheckConstraint(
            "employment_type IS NULL OR "
            + _in_list("employment_type", tuple(s.value for s in EmploymentType)),
            name="ck_applications_employment_type",
        ),
        CheckConstraint(
            f"hiring_type IS NULL OR {_in_list('hiring_type', tuple(s.value for s in HiringType))}",
            name="ck_applications_hiring_type",
        ),
        UniqueConstraint(
            "user_id", "company_id", "title", name="uq_applications_user_company_title"
        ),
        Index("ix_applications_user_status", "user_id", "status"),
        Index("ix_applications_user_deadline", "user_id", "deadline_at"),
        Index("ix_applications_user_applied", "user_id", "applied_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    track_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("tracks.id", ondelete="SET NULL"))
    resume_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL")
    )

    title: Mapped[str] = mapped_column(String(300), nullable=False)  # "회사 - 포지션"
    position: Mapped[str] = mapped_column(String(200), nullable=False)  # 공고에 적힌 직무명 그대로
    posting_url: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="discovered")
    end_stage: Mapped[str | None] = mapped_column(String(30))  # 탈락/포기일 때만
    employment_type: Mapped[str | None] = mapped_column(String(30))
    hiring_type: Mapped[str | None] = mapped_column(String(30))

    discovered_at: Mapped[date | None] = mapped_column(Date)
    applied_at: Mapped[date | None] = mapped_column(Date)
    deadline_at: Mapped[date | None] = mapped_column(Date)
    next_event_at: Mapped[datetime | None] = mapped_column(
        DateTime
    )  # 코테·면접·발표일 등 다음 일정
    next_action: Mapped[str | None] = mapped_column(String(500))  # 내가 해야 할 일 한 줄
    retrospective: Mapped[str | None] = mapped_column(Text)  # 결과 났을 때 한 줄 회고

    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    company: Mapped["Company"] = relationship(back_populates="applications", lazy="selectin")
    track: Mapped["Track | None"] = relationship(lazy="selectin")
    resume_document: Mapped["Document | None"] = relationship(lazy="selectin")
    history: Mapped[list["ApplicationStatusHistory"]] = relationship(
        back_populates="application",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ApplicationStatusHistory.changed_at",
    )


class ApplicationStatusHistory(Base):
    """상태 전환 이력. '14일 내 탈락 3회' 같은 신호는 updated_at 으로 못 잡아서 필요하다.
    임포트로 들어온 행은 source='import' 로 남겨 신호 계산에서 제외한다."""

    __tablename__ = "application_status_history"
    __table_args__ = (
        CheckConstraint(_in_list("source", HISTORY_SOURCES), name="ck_app_history_source"),
        Index("ix_app_history_app_changed", "application_id", "changed_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(String(30))
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    note: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="user")

    application: Mapped["Application"] = relationship(back_populates="history")
