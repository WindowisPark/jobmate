"""지원 트래커 API 스키마."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.application import (
    ApplicationStatus,
    EmploymentType,
    EndStage,
    HiringType,
)


# ---------------------------------------------------------------- 회사 · 트랙 · 문서
class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    industry: str | None = Field(default=None, max_length=100)
    size: str | None = Field(default=None, max_length=50)
    website: str | None = Field(default=None, max_length=500)
    memo: str | None = None

    @field_validator("name")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("회사명을 입력해주세요")
        return v


class CompanyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    industry: str | None = None
    size: str | None = None
    website: str | None = None
    memo: str | None = None


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    industry: str | None = None
    size: str | None = None
    website: str | None = None
    memo: str | None = None
    application_count: int = 0


class CompanyRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str


class TrackCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    sort_order: int = 0


class TrackUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    sort_order: int | None = None


class TrackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    color: str | None = None
    sort_order: int = 0


DOC_TYPE_PATTERN = r"^(resume|cover_letter|portfolio|experience|other)$"


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    doc_type: str = Field(default="resume", pattern=DOC_TYPE_PATTERN)
    content: str | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    doc_type: str
    created_at: datetime
    updated_at: datetime


class DocumentRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    doc_type: str = "resume"
    doc_type_label: str | None = None


class DocumentInput(BaseModel):
    """지원에 붙일 제출물 하나. id 가 오면 소유권 확인, title 이 오면 get-or-create."""

    id: UUID | None = None
    title: str | None = Field(default=None, max_length=200)
    doc_type: str = Field(default="resume", pattern=DOC_TYPE_PATTERN)

    @model_validator(mode="after")
    def _need_one(self) -> "DocumentInput":
        if not self.id and not (self.title and self.title.strip()):
            raise ValueError("제출물은 id 나 제목 중 하나가 필요해요")
        return self


# ---------------------------------------------------------------- 지원
class ApplicationCreate(BaseModel):
    """company_id 또는 company_name(get-or-create) 중 하나는 필수. track/document 도 같은 방식."""

    company_id: UUID | None = None
    company_name: str | None = Field(default=None, max_length=200)
    track_id: UUID | None = None
    track_name: str | None = Field(default=None, max_length=100)
    resume_document_id: UUID | None = None
    resume_document_title: str | None = Field(default=None, max_length=200)
    # 이력서 외 제출물(포트폴리오·경험기술서 등). 주면 제출물 집합 전체를 이걸로 맞춘다.
    documents: list[DocumentInput] | None = None

    position: str = Field(min_length=1, max_length=200)
    title: str | None = Field(default=None, max_length=300)  # 비면 "{회사} - {포지션}"
    posting_url: str | None = Field(default=None, max_length=1000)
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    end_stage: EndStage | None = None
    employment_type: EmploymentType | None = None
    hiring_type: HiringType | None = None
    discovered_at: date | None = None
    applied_at: date | None = None
    deadline_at: date | None = None
    next_event_at: datetime | None = None
    next_action: str | None = Field(default=None, max_length=500)
    retrospective: str | None = None

    @model_validator(mode="after")
    def _company_required(self) -> "ApplicationCreate":
        if not self.company_id and not (self.company_name and self.company_name.strip()):
            raise ValueError("회사를 선택하거나 회사명을 입력해주세요")
        return self


class ApplicationUpdate(BaseModel):
    """상태(status/end_stage)는 여기서 못 바꾼다 — PATCH /{id}/status 로 강제."""

    company_id: UUID | None = None
    company_name: str | None = Field(default=None, max_length=200)
    track_id: UUID | None = None
    track_name: str | None = Field(default=None, max_length=100)
    clear_track: bool = False
    resume_document_id: UUID | None = None
    resume_document_title: str | None = Field(default=None, max_length=200)
    clear_resume_document: bool = False
    documents: list[DocumentInput] | None = None  # 주면 제출물 집합 전체를 대체
    clear_documents: bool = False

    position: str | None = Field(default=None, min_length=1, max_length=200)
    title: str | None = Field(default=None, max_length=300)
    posting_url: str | None = Field(default=None, max_length=1000)
    employment_type: EmploymentType | None = None
    hiring_type: HiringType | None = None
    discovered_at: date | None = None
    applied_at: date | None = None
    deadline_at: date | None = None
    next_event_at: datetime | None = None
    next_action: str | None = Field(default=None, max_length=500)
    retrospective: str | None = None


class StatusChange(BaseModel):
    status: ApplicationStatus
    end_stage: EndStage | None = None
    note: str | None = Field(default=None, max_length=500)


class HistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    from_status: str | None
    to_status: str
    changed_at: datetime
    note: str | None = None
    source: str


class ApplicationOut(BaseModel):
    id: UUID
    title: str
    position: str
    posting_url: str | None
    status: str
    status_label: str
    end_stage: str | None
    end_stage_label: str | None
    employment_type: str | None
    employment_label: str | None
    hiring_type: str | None
    hiring_label: str | None
    discovered_at: date | None
    applied_at: date | None
    deadline_at: date | None
    next_event_at: datetime | None
    next_action: str | None
    retrospective: str | None
    created_at: datetime
    updated_at: datetime
    # 파생
    d_day: int | None
    season: str | None
    is_active: bool
    is_applied: bool
    passed_docs: bool
    reached_interview: bool
    company: CompanyRef
    track: TrackOut | None
    documents: list[DocumentRef]
    resume_document: DocumentRef | None  # documents 중 이력서 종류의 첫 번째(파생)


class ApplicationDetailOut(ApplicationOut):
    history: list[HistoryOut]


class ApplicationListOut(BaseModel):
    items: list[ApplicationOut]
    total: int


class StatusChangeOut(BaseModel):
    application: ApplicationOut
    celebration: bool


class SeasonStat(BaseModel):
    season: str
    total: int
    applied: int
    passed_docs: int
    interview: int
    offer: int


class TrackStat(BaseModel):
    track_id: UUID | None
    track_name: str
    total: int
    applied: int
    passed_docs: int
    interview: int
    offer: int


class DocumentStat(BaseModel):
    """제출물 버전별 승률 — 자소서가 빠진 전형에서 '무엇을 냈나'를 가르는 축."""

    document_id: UUID
    title: str
    doc_type: str
    doc_type_label: str
    total: int
    applied: int
    passed_docs: int
    interview: int
    offer: int


class StatsOut(BaseModel):
    by_status: dict[str, int]
    by_season: list[SeasonStat]
    by_track: list[TrackStat]
    by_document: list[DocumentStat]
    funnel: dict[str, int]  # applied / passed_docs / interview / offer
    active_count: int
    total: int


# ---------------------------------------------------------------- 임포트
class ImportRowError(BaseModel):
    row: int
    field: str | None
    reason: str
    raw: str | None = None


class ImportReport(BaseModel):
    dry_run: bool
    total_rows: int
    created: int
    updated: int
    skipped: int
    errors: list[ImportRowError]
    preview: list[dict]
