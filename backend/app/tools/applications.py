"""지원 트래커 도구 — 에이전트가 내 지원 현황을 읽고 고칠 수 있게 한다.

채팅에서 "카카오 서류 탈락했어" 라고 말하면 보드가 갱신되는 경로가 여기다.
DB 세션과 user_id 는 서버가 채운다(`agents/nodes/_tool_exec.py`).
"""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import ACTIVE_STATUSES, STATUS_LABELS, Application
from app.services import application_service as svc

MAX_LIMIT = 20
AMBIGUOUS_LIMIT = 5


def _brief(app: Application, today) -> dict:
    return {
        "application_id": str(app.id),
        "company": app.company.name,
        "position": app.position,
        "status": app.status,
        "status_label": STATUS_LABELS.get(app.status, app.status),
        "d_day": svc.d_day(app.deadline_at, today),
        "deadline_at": app.deadline_at.isoformat() if app.deadline_at else None,
        "next_action": app.next_action,
        "documents": [d.title for d in app.documents],
    }


async def get_my_applications(
    status: str | None = None,
    only_urgent: bool = False,
    query: str | None = None,
    limit: int = 10,
    *,
    db: AsyncSession,
    user_id: str,
) -> dict:
    """사용자의 지원 현황을 조회합니다."""
    today = svc.today_kst()
    stmt = select(Application).where(Application.user_id == uuid.UUID(user_id))
    if status:
        stmt = stmt.where(Application.status == status)
    if query:
        like = f"%{query.strip()}%"
        stmt = stmt.where(or_(Application.title.ilike(like), Application.position.ilike(like)))

    rows = list((await db.execute(stmt)).scalars().all())
    if only_urgent:
        rows = [
            a
            for a in rows
            if a.status in ACTIVE_STATUSES
            and a.deadline_at
            and 0 <= (a.deadline_at - today).days <= svc.URGENT_DDAY
        ]
    rows.sort(key=lambda a: (a.deadline_at is None, a.deadline_at or today))

    items = [_brief(a, today) for a in rows[: min(limit, MAX_LIMIT)]]
    active = sum(1 for a in rows if a.status in ACTIVE_STATUSES)
    return {
        "total": len(rows),
        "active_count": active,
        "items": items,
        "summary_line": f"조회 {len(rows)}건, 진행 중 {active}건",
    }


async def update_application_status(
    status: str,
    application_id: str | None = None,
    title_query: str | None = None,
    end_stage: str | None = None,
    note: str | None = None,
    *,
    db: AsyncSession,
    user_id: str,
) -> dict:
    """지원 상태를 변경합니다."""
    uid = uuid.UUID(user_id)

    if application_id:
        try:
            target_id = uuid.UUID(application_id)
        except ValueError:
            return {"error": "지원 id 형식이 올바르지 않아요"}
        stmt = select(Application).where(Application.id == target_id, Application.user_id == uid)
        matches = list((await db.execute(stmt)).scalars().all())
    elif title_query:
        like = f"%{title_query.strip()}%"
        stmt = select(Application).where(Application.user_id == uid, Application.title.ilike(like))
        matches = list((await db.execute(stmt)).scalars().all())
    else:
        return {"error": "어떤 지원인지 알려주세요"}

    if not matches:
        return {"error": "그런 지원을 찾지 못했어요", "found": 0}

    if len(matches) > 1:
        # 여러 건이면 고르지 않는다. 되물어야 한다.
        today = svc.today_kst()
        return {
            "ambiguous": [_brief(a, today) for a in matches[:AMBIGUOUS_LIMIT]],
            "message": "어느 지원인지 하나만 골라주세요",
        }

    app = matches[0]
    try:
        celebrate = svc.change_status(db, app, status, end_stage, note=note, source="agent")
    except svc.StatusChangeError as e:
        return {"error": str(e), "needs_end_stage": True}

    await db.flush()
    label = STATUS_LABELS.get(app.status, app.status)
    return {
        "status": "updated",
        "application_id": str(app.id),
        "company": app.company.name,
        "from_status": None,
        "to_status": app.status,
        "status_label": label,
        "celebration": celebrate,
        "message": f"{app.company.name} 상태를 {label}로 바꿨어요",
    }
