"""노션 "📝 지원" DB CSV 임포트.

노션 CSV 내보내기 규격: UTF-8 BOM, 헤더는 속성명(한글) 그대로, 관계(relation)는 "이름 (https://www.notion.so/...)" 형태가
쉼표로 이어짐, 날짜는 워크스페이스 언어에 따라 "September 9, 2026" / "2026년 9월 9일" / ISO 가 섞인다.
수식 열(D-day·시즌·지원N·서류통과N·면접N)은 무시한다.
"""

from __future__ import annotations

import csv
import io
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import (
    CLOSED_WITH_STAGE,
    EMPLOYMENT_LABELS,
    END_STAGE_LABELS,
    HIRING_LABELS,
    STATUS_LABELS,
    Application,
    ApplicationStatusHistory,
    Company,
    Document,
    Track,
)
from app.services.application_service import default_title

HEADER_MAP: dict[str, str] = {
    "제목": "title",
    "회사": "company_name",
    "포지션": "position",
    "트랙": "track_name",
    "공고 URL": "posting_url",
    "상태": "status",
    "종료단계": "end_stage",
    "고용형태": "employment_type",
    "채용방식": "hiring_type",
    "발견일": "discovered_at",
    "지원일": "applied_at",
    "마감일": "deadline_at",
    "다음 일정": "next_event_at",
    "다음 액션": "next_action",
    "한 줄 회고": "retrospective",
    "이력서 버전": "resume_document_title",
}
REQUIRED_HEADERS = ("회사", "포지션")
IGNORED_HEADERS = {"D-day", "시즌", "지원N", "서류통과N", "면접N", "생성일"}

STATUS_KO = {v: k for k, v in STATUS_LABELS.items()}
END_STAGE_KO = {v: k for k, v in END_STAGE_LABELS.items()}
EMPLOYMENT_KO = {v: k for k, v in EMPLOYMENT_LABELS.items()}
HIRING_KO = {v: k for k, v in HIRING_LABELS.items()}

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 2000

_NOTION_LINK = re.compile(r"\s*\((?:https?://)?(?:www\.)?notion\.(?:so|site)/[^)]*\)\s*$")
_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d",
    "%Y.%m.%d",
    "%Y. %m. %d.",
    "%B %d, %Y",
    "%B %d, %Y %I:%M %p",
    "%b %d, %Y",
    "%b %d, %Y %I:%M %p",
    "%Y년 %m월 %d일",
    "%Y년 %m월 %d일 %H:%M",
    "%Y년 %m월 %d일 %p %I:%M",
)


class RowError(Exception):
    def __init__(self, field_: str | None, reason: str, raw: str | None = None):
        super().__init__(reason)
        self.field = field_
        self.reason = reason
        self.raw = raw


def first_relation(value: str | None) -> str | None:
    """'백엔드 (https://www.notion.so/abc), 데이터 (...)' → '백엔드'."""
    if not value:
        return None
    first = value.split(", ")[0].strip()
    first = _NOTION_LINK.sub("", first).strip()
    return first or None


def parse_notion_date(value: str | None, field_: str) -> datetime | None:
    """범위('A → B')면 앞부분. 시간이 없으면 00:00. 실패 시 RowError."""
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None
    if "→" in raw:
        raw = raw.split("→")[0].strip()
    raw = raw.replace("오전", "AM").replace("오후", "PM")
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise RowError(field_, f"날짜 형식을 알 수 없어요: {raw}", raw)


def map_select(
    value: str | None, table: dict[str, str], field_: str, *, default: str | None = None
) -> str | None:
    if value is None or not value.strip():
        return default
    v = value.strip()
    if v in table:
        return table[v]
    if v in table.values():  # 이미 영문 키로 들어온 경우
        return v
    raise RowError(field_, f"알 수 없는 {field_} 값: {v}", v)


@dataclass
class NormalizedRow:
    company_name: str
    position: str
    title: str
    track_name: str | None = None
    posting_url: str | None = None
    status: str = "discovered"
    end_stage: str | None = None
    employment_type: str | None = None
    hiring_type: str | None = None
    discovered_at: date | None = None
    applied_at: date | None = None
    deadline_at: date | None = None
    next_event_at: datetime | None = None
    next_action: str | None = None
    retrospective: str | None = None
    resume_document_title: str | None = None
    warnings: list[str] = field(default_factory=list)

    def preview(self) -> dict:
        return {
            "company": self.company_name,
            "position": self.position,
            "title": self.title,
            "track": self.track_name,
            "status": STATUS_LABELS.get(self.status, self.status),
            "end_stage": END_STAGE_LABELS.get(self.end_stage) if self.end_stage else None,
            "deadline_at": self.deadline_at.isoformat() if self.deadline_at else None,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
            "resume": self.resume_document_title,
            "warnings": self.warnings,
        }


def normalize_row(raw: dict[str, str]) -> NormalizedRow:
    row = {
        HEADER_MAP[k.strip()]: (v or "").strip()
        for k, v in raw.items()
        if k and k.strip() in HEADER_MAP
    }
    company = first_relation(row.get("company_name"))
    position = row.get("position") or ""
    title = row.get("title") or ""

    # 회사가 비었는데 제목이 "회사 - 포지션" 꼴이면 거기서 복원
    if not company and " - " in title:
        company = title.split(" - ", 1)[0].strip()
    if not position and " - " in title:
        position = title.split(" - ", 1)[1].strip()
    if not company:
        raise RowError("회사", "회사가 비어 있어요", title or None)
    if not position:
        raise RowError("포지션", "포지션이 비어 있어요", title or None)
    if not title:
        title = default_title(company, position)

    status = map_select(row.get("status"), STATUS_KO, "상태", default="discovered") or "discovered"
    end_stage = map_select(row.get("end_stage"), END_STAGE_KO, "종료단계")
    warnings: list[str] = []
    if end_stage and status not in CLOSED_WITH_STAGE:
        warnings.append(
            f"종료단계({END_STAGE_LABELS[end_stage]})는 탈락/포기에서만 유효해 버렸어요"
        )
        end_stage = None

    def as_date(key: str, label: str) -> date | None:
        dt = parse_notion_date(row.get(key), label)
        return dt.date() if dt else None

    next_event = parse_notion_date(row.get("next_event_at"), "다음 일정")
    if next_event and next_event.hour == 0 and next_event.minute == 0:
        next_event = next_event.replace(hour=9)  # 시간 없는 일정은 09:00 로

    return NormalizedRow(
        company_name=company,
        position=position,
        title=title,
        track_name=first_relation(row.get("track_name")),
        posting_url=row.get("posting_url") or None,
        status=status,
        end_stage=end_stage,
        employment_type=map_select(row.get("employment_type"), EMPLOYMENT_KO, "고용형태"),
        hiring_type=map_select(row.get("hiring_type"), HIRING_KO, "채용방식"),
        discovered_at=as_date("discovered_at", "발견일"),
        applied_at=as_date("applied_at", "지원일"),
        deadline_at=as_date("deadline_at", "마감일"),
        next_event_at=next_event,
        next_action=row.get("next_action") or None,
        retrospective=row.get("retrospective") or None,
        resume_document_title=first_relation(row.get("resume_document_title")),
        warnings=warnings,
    )


def dedupe_key(company: str, title: str) -> tuple[str, str]:
    return (company.strip().casefold(), title.strip().casefold())


def read_csv(content: bytes) -> tuple[list[str], list[dict[str, str]]]:
    if len(content) > MAX_BYTES:
        raise ValueError("CSV는 2MB 이하만 받아요")
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    headers = [h.strip() for h in (reader.fieldnames or [])]
    missing = [h for h in REQUIRED_HEADERS if h not in headers and "제목" not in headers]
    if missing:
        raise ValueError(f"필수 열 누락: {', '.join(missing)}")
    rows = list(reader)
    if len(rows) > MAX_ROWS:
        raise ValueError(f"행이 너무 많아요 ({len(rows)} > {MAX_ROWS})")
    return headers, rows


async def import_notion_csv(
    db: AsyncSession,
    user_id: uuid.UUID,
    content: bytes,
    *,
    dry_run: bool = True,
    on_duplicate: str = "skip",
) -> dict:
    """행을 정규화해 upsert 한다. 커밋/롤백은 호출자가 한다(dry_run 이면 롤백)."""
    _, raw_rows = read_csv(content)

    existing_q = await db.execute(select(Application).where(Application.user_id == user_id))
    existing: dict[tuple[str, str], Application] = {
        dedupe_key(a.company.name, a.title): a for a in existing_q.scalars().all()
    }
    companies: dict[str, Company] = {}
    tracks: dict[str, Track] = {}
    docs: dict[str, Document] = {}

    async def company_for(name: str) -> Company:
        k = name.casefold()
        if k not in companies:
            r = await db.execute(select(Company).where(Company.user_id == user_id))
            for c in r.scalars().all():
                companies.setdefault(c.name.casefold(), c)
            if k not in companies:
                c = Company(user_id=user_id, name=name)
                db.add(c)
                await db.flush()
                companies[k] = c
        return companies[k]

    async def track_for(name: str) -> Track:
        k = name.casefold()
        if k not in tracks:
            r = await db.execute(select(Track).where(Track.user_id == user_id))
            for t in r.scalars().all():
                tracks.setdefault(t.name.casefold(), t)
            if k not in tracks:
                t = Track(user_id=user_id, name=name, sort_order=len(tracks))
                db.add(t)
                await db.flush()
                tracks[k] = t
        return tracks[k]

    async def doc_for(title: str) -> Document:
        k = title.casefold()
        if k not in docs:
            r = await db.execute(select(Document).where(Document.user_id == user_id))
            for d in r.scalars().all():
                docs.setdefault(d.title.casefold(), d)
            if k not in docs:
                d = Document(user_id=user_id, title=title, doc_type="resume")
                db.add(d)
                await db.flush()
                docs[k] = d
        return docs[k]

    created = updated = skipped = 0
    errors: list[dict] = []
    preview: list[dict] = []

    for idx, raw in enumerate(raw_rows, start=2):  # 1행은 헤더
        try:
            row = normalize_row(raw)
        except RowError as e:
            errors.append({"row": idx, "field": e.field, "reason": e.reason, "raw": e.raw})
            continue
        if len(preview) < 10:
            preview.append(row.preview())

        company = await company_for(row.company_name)
        track = await track_for(row.track_name) if row.track_name else None
        doc = await doc_for(row.resume_document_title) if row.resume_document_title else None
        key = dedupe_key(company.name, row.title)
        history_at = datetime.combine(
            row.applied_at or row.discovered_at or date.today(), datetime.min.time()
        )

        app = existing.get(key)
        if app is None:
            app = Application(
                user_id=user_id,
                company_id=company.id,
                track_id=track.id if track else None,
                resume_document_id=doc.id if doc else None,
                title=row.title,
                position=row.position,
                posting_url=row.posting_url,
                status=row.status,
                end_stage=row.end_stage,
                employment_type=row.employment_type,
                hiring_type=row.hiring_type,
                discovered_at=row.discovered_at,
                applied_at=row.applied_at,
                deadline_at=row.deadline_at,
                next_event_at=row.next_event_at,
                next_action=row.next_action,
                retrospective=row.retrospective,
            )
            db.add(app)
            await db.flush()
            db.add(
                ApplicationStatusHistory(
                    application_id=app.id,
                    from_status=None,
                    to_status=row.status,
                    changed_at=history_at,
                    source="import",
                )
            )
            existing[key] = app
            created += 1
            continue

        if on_duplicate != "update":
            skipped += 1
            continue

        prev_status = app.status
        for name in (
            "position",
            "posting_url",
            "employment_type",
            "hiring_type",
            "discovered_at",
            "applied_at",
            "deadline_at",
            "next_event_at",
            "next_action",
            "retrospective",
        ):
            v = getattr(row, name)
            if v is not None:
                setattr(app, name, v)
        if track:
            app.track_id = track.id
        if doc:
            app.resume_document_id = doc.id
        if row.status != prev_status:
            app.status = row.status
            app.end_stage = row.end_stage
            db.add(
                ApplicationStatusHistory(
                    application_id=app.id,
                    from_status=prev_status,
                    to_status=row.status,
                    changed_at=history_at,
                    source="import",
                )
            )
        updated += 1

    await db.flush()
    return {
        "dry_run": dry_run,
        "total_rows": len(raw_rows),
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "preview": preview,
    }
