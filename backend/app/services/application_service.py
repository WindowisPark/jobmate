"""지원 트래커 서비스 — 파생 필드(D-day·시즌·단계), 상태 전환, 조회, 요약 신호.

API(applications.py) · 월드 신호(world.py) · LangGraph 컨텍스트(chat.py) 가 전부 이 모듈을 쓴다
(단일 진실).
D-day 는 요청 시각(KST)에 의존하므로 SQL 뷰가 아니라 여기서 계산한다.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import (
    ACTIVE_STATUSES,
    CLOSED_WITH_STAGE,
    DOC_TYPE_LABELS,
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

KST = timezone(timedelta(hours=9))  # DST 없음 — tzdata 의존 없이 고정 오프셋

# 단계 순위 — 노션의 지원N/서류통과N/면접N 수식을 행 단위 boolean 으로 재현하기 위한 축
STATUS_RANK: dict[str, int] = {
    "not_applied": 0,
    "discovered": 0,
    "reviewing": 1,
    "applied": 2,
    "no_response": 2,
    "doc_passed": 3,
    "coding_test": 4,
    "assignment": 4,
    "interview": 5,
    "offer": 6,
}
# 종결 상태(탈락/포기)는 종료단계로 도달 단계를 환산
END_STAGE_RANK: dict[str, int] = {
    "document": 2,
    "coding_test": 3,
    "written_test": 3,
    "assignment": 3,
    "interview": 5,
    "final": 6,
}

URGENT_DDAY = 3  # 이 이하면 "마감 임박"
RECENT_DAYS = 14  # 최근 결과 창
REJECTION_STREAK_MIN = 3  # 이 이상이면 멘탈 케어 개입


class StatusChangeError(ValueError):
    """잘못된 상태 전환(422 로 매핑)."""


# ---------------------------------------------------------------- 순수 함수
def today_kst() -> date:
    return datetime.now(KST).date()


def d_day(deadline: date | None, today: date | None = None) -> int | None:
    if deadline is None:
        return None
    return (deadline - (today or today_kst())).days


def season_of(
    applied_at: date | None, deadline_at: date | None, discovered_at: date | None
) -> str | None:
    """기준일 = 지원일 → 마감일 → 발견일. 1~6월 상반기, 7~12월 하반기."""
    base = applied_at or deadline_at or discovered_at
    if base is None:
        return None
    return f"{base.year} {'상반기' if base.month <= 6 else '하반기'}"


def season_range(season: str) -> tuple[date, date] | None:
    """'2026 상반기' → (2026-01-01, 2026-06-30). 형식이 다르면 None."""
    parts = season.strip().split()
    if len(parts) != 2 or not parts[0].isdigit() or parts[1] not in ("상반기", "하반기"):
        return None
    year = int(parts[0])
    return (
        (date(year, 1, 1), date(year, 6, 30))
        if parts[1] == "상반기"
        else (date(year, 7, 1), date(year, 12, 31))
    )


def reached_rank(status: str, end_stage: str | None) -> int:
    """이 지원이 어느 단계까지 도달했는지(0~6)."""
    if status in CLOSED_WITH_STAGE and end_stage:
        return END_STAGE_RANK.get(end_stage, 2)
    if status in CLOSED_WITH_STAGE:
        return 2  # 종료단계 미기록 탈락/포기는 '지원은 했다'로 본다
    return STATUS_RANK.get(status, 0)


def validate_status_change(status: str, end_stage: str | None) -> str | None:
    """종료단계 규칙을 검사하고 저장할 end_stage 를 돌려준다. 위반 시 StatusChangeError."""
    if status in CLOSED_WITH_STAGE:
        if not end_stage:
            raise StatusChangeError("탈락·포기는 어느 단계에서 끝났는지(종료단계)를 선택해주세요")
        return end_stage
    return None  # 그 외 상태는 서버가 초기화


def default_title(company_name: str, position: str) -> str:
    return f"{company_name.strip()} - {position.strip()}"


# ---------------------------------------------------------------- 제출물
def doc_ref(doc: Document) -> dict:
    return {
        "id": doc.id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "doc_type_label": DOC_TYPE_LABELS.get(doc.doc_type, doc.doc_type),
    }


def primary_resume(app: Application) -> Document | None:
    """'이 지원의 이력서' — 붙은 제출물 중 이력서 종류의 첫 번째.

    단일 FK 를 조인 테이블로 바꾸면서 생긴 파생 값. 기존 API 응답 모양을 유지한다.
    """
    return next((d for d in app.documents if d.doc_type == "resume"), None)


# ---------------------------------------------------------------- 직렬화
def to_out(app: Application, today: date | None = None) -> dict:
    today = today or today_kst()
    rank = reached_rank(app.status, app.end_stage)
    return {
        "id": app.id,
        "title": app.title,
        "position": app.position,
        "posting_url": app.posting_url,
        "status": app.status,
        "status_label": STATUS_LABELS.get(app.status, app.status),
        "end_stage": app.end_stage,
        "end_stage_label": END_STAGE_LABELS.get(app.end_stage) if app.end_stage else None,
        "employment_type": app.employment_type,
        "employment_label": EMPLOYMENT_LABELS.get(app.employment_type)
        if app.employment_type
        else None,
        "hiring_type": app.hiring_type,
        "hiring_label": HIRING_LABELS.get(app.hiring_type) if app.hiring_type else None,
        "discovered_at": app.discovered_at,
        "applied_at": app.applied_at,
        "deadline_at": app.deadline_at,
        "next_event_at": app.next_event_at,
        "next_action": app.next_action,
        "retrospective": app.retrospective,
        "created_at": app.created_at,
        "updated_at": app.updated_at,
        "d_day": d_day(app.deadline_at, today),
        "season": season_of(app.applied_at, app.deadline_at, app.discovered_at),
        "is_active": app.status in ACTIVE_STATUSES,
        "is_applied": rank >= 2,
        "passed_docs": rank >= 3,
        "reached_interview": rank >= 5,
        "company": {"id": app.company.id, "name": app.company.name},
        "track": (
            {
                "id": app.track.id,
                "name": app.track.name,
                "color": app.track.color,
                "sort_order": app.track.sort_order,
            }
            if app.track
            else None
        ),
        "documents": [doc_ref(d) for d in app.documents],
        "resume_document": (doc_ref(resume) if (resume := primary_resume(app)) else None),
    }


# ---------------------------------------------------------------- get-or-create
async def get_or_create_company(db: AsyncSession, user_id: uuid.UUID, name: str) -> Company:
    name = name.strip()
    result = await db.execute(
        select(Company).where(Company.user_id == user_id, func.lower(Company.name) == name.lower())
    )
    company = result.scalar_one_or_none()
    if company is None:
        company = Company(user_id=user_id, name=name)
        db.add(company)
        await db.flush()
    return company


async def get_or_create_track(db: AsyncSession, user_id: uuid.UUID, name: str) -> Track:
    name = name.strip()
    result = await db.execute(
        select(Track).where(Track.user_id == user_id, func.lower(Track.name) == name.lower())
    )
    track = result.scalar_one_or_none()
    if track is None:
        count = (
            await db.scalar(select(func.count()).select_from(Track).where(Track.user_id == user_id))
            or 0
        )
        track = Track(user_id=user_id, name=name, sort_order=count)
        db.add(track)
        await db.flush()
    return track


async def get_or_create_document(
    db: AsyncSession, user_id: uuid.UUID, title: str, doc_type: str = "resume"
) -> Document:
    title = title.strip()
    result = await db.execute(
        select(Document).where(
            Document.user_id == user_id, func.lower(Document.title) == title.lower()
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        doc = Document(user_id=user_id, title=title, doc_type=doc_type)
        db.add(doc)
        await db.flush()
    return doc


def attach_document(app: Application, doc: Document) -> bool:
    """제출물을 지원에 붙인다. 이미 붙어 있으면 False.

    연결 행(application_documents)은 secondary 관계가 관리하므로 컬렉션만 건드린다.
    직접 INSERT 하면 같은 행을 두 번 넣어 UNIQUE 제약에 걸린다.
    """
    if any(d.id == doc.id for d in app.documents):
        return False
    app.documents.append(doc)
    return True


def detach_document(app: Application, doc_id: uuid.UUID) -> bool:
    """연결만 끊는다. 문서 자체는 남긴다(다른 지원이 쓰고 있을 수 있다)."""
    before = len(app.documents)
    app.documents[:] = [d for d in app.documents if d.id != doc_id]
    return len(app.documents) != before


def set_documents(app: Application, docs: list[Document]) -> None:
    """제출물 집합 전체를 교체한다."""
    app.documents[:] = list(docs)


def replace_resume(app: Application, doc: Document | None) -> None:
    """'이력서 버전' 슬롯 하나만 갈아끼운다. 포트폴리오·경험기술서 연결은 건드리지 않는다."""
    keep_id = doc.id if doc else None
    app.documents[:] = [d for d in app.documents if d.doc_type != "resume" or d.id == keep_id]
    if doc and not any(d.id == doc.id for d in app.documents):
        app.documents.append(doc)


# ---------------------------------------------------------------- 상태 전환
def record_history(
    db: AsyncSession,
    app: Application,
    from_status: str | None,
    to_status: str,
    *,
    source: str = "user",
    note: str | None = None,
    changed_at: datetime | None = None,
) -> ApplicationStatusHistory:
    """이력 행을 세션에 직접 넣는다. app.history 에 append 하면 async 세션에서 지연 로딩이 터진다."""
    h = ApplicationStatusHistory(
        application_id=app.id,
        from_status=from_status,
        to_status=to_status,
        changed_at=changed_at or datetime.utcnow(),
        note=note,
        source=source,
    )
    db.add(h)
    return h


def apply_status(
    app: Application, status: str, end_stage: str | None, *, today: date | None = None
) -> tuple[str, bool]:
    """순수 상태 갱신. (이전 상태, 최종합격 전환 여부) 반환. 위반 시 StatusChangeError."""
    saved_stage = validate_status_change(status, end_stage)
    prev = app.status
    app.status = status
    app.end_stage = saved_stage
    if status == "applied" and app.applied_at is None:
        app.applied_at = today or today_kst()
    return prev, status == "offer" and prev != "offer"


def change_status(
    db: AsyncSession,
    app: Application,
    status: str,
    end_stage: str | None,
    *,
    note: str | None = None,
    source: str = "user",
    today: date | None = None,
) -> bool:
    """상태를 바꾸고 이력을 남긴다. 최종합격 전환이면 True(축하 연출용)."""
    prev, celebrate = apply_status(app, status, end_stage, today=today)
    if prev != status or note:
        record_history(db, app, prev if prev != status else None, status, source=source, note=note)
    return celebrate


# ---------------------------------------------------------------- 요약 신호 (world · chat 공용)
async def build_application_summary(
    db: AsyncSession, user_id: uuid.UUID, today: date | None = None
) -> dict:
    """유저의 지원 현황을 '방이 반응할 신호'로 압축한다. LLM 컨텍스트와 월드 상태가 같은 dict 를 쓴다."""
    today = today or today_kst()
    result = await db.execute(select(Application).where(Application.user_id == user_id))
    apps = list(result.scalars().all())

    active = [a for a in apps if a.status in ACTIVE_STATUSES]
    stage_counts: dict[str, int] = {}
    for a in apps:
        stage_counts[a.status] = stage_counts.get(a.status, 0) + 1

    def brief(a: Application) -> dict:
        return {
            "application_id": str(a.id),
            "title": a.title,
            "company": a.company.name,
            "position": a.position,
            "status": a.status,
            "status_label": STATUS_LABELS.get(a.status, a.status),
            "deadline_at": a.deadline_at.isoformat() if a.deadline_at else None,
            "d_day": d_day(a.deadline_at, today),
            "next_event_at": a.next_event_at.isoformat() if a.next_event_at else None,
            "next_action": a.next_action,
            "resume_document": (r.title if (r := primary_resume(a)) else None),
            "documents": [d.title for d in a.documents],
        }

    urgent = sorted(
        (a for a in active if a.deadline_at and 0 <= (a.deadline_at - today).days <= URGENT_DDAY),
        key=lambda a: a.deadline_at,  # type: ignore[arg-type,return-value]
    )
    overdue = sorted(
        (a for a in active if a.deadline_at and (a.deadline_at - today).days < 0),
        key=lambda a: a.deadline_at,  # type: ignore[arg-type,return-value]
    )
    upcoming = sorted(
        (a for a in active if a.next_event_at and a.next_event_at >= datetime.now()),
        key=lambda a: a.next_event_at,  # type: ignore[arg-type,return-value]
    )

    # 최근 결과: 유저/에이전트가 바꾼 이력만(임포트 제외) — 탈락 스트릭 오발 방지
    since = datetime.utcnow() - timedelta(days=RECENT_DAYS)
    hist_rows = await db.execute(
        select(ApplicationStatusHistory)
        .join(Application, Application.id == ApplicationStatusHistory.application_id)
        .where(
            Application.user_id == user_id,
            ApplicationStatusHistory.changed_at >= since,
            ApplicationStatusHistory.source != "import",
            ApplicationStatusHistory.to_status.in_(["rejected", "offer"]),
        )
        .order_by(ApplicationStatusHistory.changed_at.desc())
    )
    hist = list(hist_rows.scalars().all())
    by_id = {a.id: a for a in apps}
    recent_outcomes = [
        {
            "application_id": str(h.application_id),
            "title": by_id[h.application_id].title if h.application_id in by_id else "",
            "to_status": h.to_status,
            "changed_at": h.changed_at.isoformat(),
        }
        for h in hist
    ]
    rejection_streak = sum(1 for h in hist if h.to_status == "rejected")
    recent_offer = next(
        (
            h
            for h in hist
            if h.to_status == "offer" and h.changed_at >= datetime.utcnow() - timedelta(days=3)
        ),
        None,
    )

    return {
        "today": today.isoformat(),
        "total": len(apps),
        "active_count": len(active),
        "stage_counts": stage_counts,
        "urgent_deadlines": [brief(a) for a in urgent],
        "overdue": [brief(a) for a in overdue],
        "next_event": brief(upcoming[0]) if upcoming else None,
        "recent_outcomes": recent_outcomes,
        "rejection_streak_14d": rejection_streak,
        "celebration": (
            {
                "application_id": str(recent_offer.application_id),
                "title": by_id[recent_offer.application_id].title,
            }
            if recent_offer and recent_offer.application_id in by_id
            else None
        ),
    }


def format_application_context(summary: dict, agent_id: str, limit: int = 500) -> str:
    """LangGraph 노드 프롬프트용 한 문단. 에이전트별로 관점을 다르게 준다."""
    if not summary or summary.get("total", 0) == 0:
        return ""
    lines: list[str] = []
    if agent_id in ("jun_ho", "seo_yeon"):
        for a in summary.get("urgent_deadlines", [])[:3]:
            doc = f", 이력서 {a['resume_document']}" if a.get("resume_document") else ""
            lines.append(f"- 마감 D-{a['d_day']}: {a['company']} {a['position']}{doc}")
        nxt = summary.get("next_event")
        if nxt and nxt.get("next_event_at"):
            lines.append(
                f"- 다음 일정: {nxt['company']} {nxt['status_label']} {nxt['next_event_at'][:16]}"
            )
        if summary.get("overdue"):
            lines.append(f"- 마감 지난 활성 지원 {len(summary['overdue'])}건")
    elif agent_id == "ha_eun":
        streak = summary.get("rejection_streak_14d", 0)
        if streak:
            lines.append(f"- 최근 2주 탈락 {streak}건 (수치를 나열하지 말고 감정을 먼저 살펴줘)")
        if summary.get("celebration"):
            lines.append(f"- 최근 최종합격: {summary['celebration']['title']}")
        lines.append(f"- 진행 중 지원 {summary.get('active_count', 0)}건")
    else:  # min_su
        sc = summary.get("stage_counts", {})
        lines.append(
            "- 현황: " + ", ".join(f"{STATUS_LABELS.get(k, k)} {v}" for k, v in sc.items() if v)
        )
        if summary.get("celebration"):
            lines.append(f"- 최근 최종합격: {summary['celebration']['title']}")
    if not lines:
        return ""
    text = "사용자의 지원 현황:\n" + "\n".join(lines)
    return text[:limit]
