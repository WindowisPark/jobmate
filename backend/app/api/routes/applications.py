"""📝 지원 대시보드 API.

노션 '지원' DB 의 5개 뷰(진행중·캘린더·시즌별·트랙별·전체)를
이 엔드포인트 + 프런트 그룹핑으로 덮는다.
"""

import uuid
from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth import get_current_user_id
from app.dependencies import get_db
from app.models.application import (
    ACTIVE_STATUSES,
    DOC_TYPE_LABELS,
    Application,
    ApplicationStatus,
    Document,
)
from app.schemas.application import (
    ApplicationCreate,
    ApplicationDetailOut,
    ApplicationListOut,
    ApplicationOut,
    ApplicationUpdate,
    DocumentInput,
    DocumentStat,
    ImportReport,
    SeasonStat,
    StatsOut,
    StatusChange,
    StatusChangeOut,
    TrackStat,
)
from app.services import application_service as svc
from app.services.notion_import import import_notion_csv

router = APIRouter()

SORTABLE = {
    "deadline_at": Application.deadline_at,
    "applied_at": Application.applied_at,
    "updated_at": Application.updated_at,
    "next_event_at": Application.next_event_at,
    "created_at": Application.created_at,
}


async def _get_owned(db: AsyncSession, user_id: uuid.UUID, app_id: uuid.UUID) -> Application:
    # populate_existing: 커밋 후 재조회할 때 identity map 에 남은 stale 관계(track/company)를 다시 채운다
    result = await db.execute(
        select(Application)
        .where(Application.id == app_id, Application.user_id == user_id)
        .execution_options(populate_existing=True)
    )
    app = result.scalar_one_or_none()
    if app is None:
        raise HTTPException(status_code=404, detail="지원 내역을 찾을 수 없어요")
    return app


async def _resolve_refs(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    company_id: uuid.UUID | None,
    company_name: str | None,
    track_id: uuid.UUID | None,
    track_name: str | None,
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    """id 가 오면 소유권 확인, 이름이 오면 get-or-create."""
    cid = tid = None
    if company_id:
        cid = (await svc_owned(db, user_id, "companies", company_id)).id
    elif company_name:
        cid = (await svc.get_or_create_company(db, user_id, company_name)).id
    if track_id:
        tid = (await svc_owned(db, user_id, "tracks", track_id)).id
    elif track_name:
        tid = (await svc.get_or_create_track(db, user_id, track_name)).id
    return cid, tid


async def _resolve_doc(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    doc_id: uuid.UUID | None,
    doc_title: str | None,
    doc_type: str = "resume",
) -> Document | None:
    if doc_id:
        return await svc_owned(db, user_id, "documents", doc_id)
    if doc_title and doc_title.strip():
        return await svc.get_or_create_document(db, user_id, doc_title, doc_type)
    return None


async def _resolve_docs(
    db: AsyncSession, user_id: uuid.UUID, items: list[DocumentInput] | None
) -> list[Document]:
    """제출물 목록을 해석한다(중복 제거, 입력 순서 유지)."""
    out: list[Document] = []
    for it in items or []:
        doc = await _resolve_doc(
            db, user_id, doc_id=it.id, doc_title=it.title, doc_type=it.doc_type
        )
        if doc and all(d.id != doc.id for d in out):
            out.append(doc)
    return out


async def svc_owned(db: AsyncSession, user_id: uuid.UUID, table: str, obj_id: uuid.UUID):
    from app.models.application import Company, Document, Track

    model = {"companies": Company, "tracks": Track, "documents": Document}[table]
    result = await db.execute(select(model).where(model.id == obj_id, model.user_id == user_id))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail=f"{table} 항목을 찾을 수 없어요")
    return obj


# ---------------------------------------------------------------- 목록 · 통계
@router.get("", response_model=ApplicationListOut)
async def list_applications(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    status: list[ApplicationStatus] | None = Query(None),
    active: bool | None = Query(None, description="true 면 진행중 상태만"),
    track_id: uuid.UUID | None = None,
    company_id: uuid.UUID | None = None,
    season: str | None = Query(None, description="예: 2026 하반기"),
    deadline_from: date | None = None,
    deadline_to: date | None = None,
    event_from: datetime | None = None,
    event_to: datetime | None = None,
    q: str | None = Query(None, max_length=100),
    sort: Literal[
        "deadline_at", "applied_at", "updated_at", "next_event_at", "created_at"
    ] = "deadline_at",
    order: Literal["asc", "desc"] = "asc",
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> ApplicationListOut:
    stmt = select(Application).where(Application.user_id == user_id)
    if status:
        stmt = stmt.where(Application.status.in_([s.value for s in status]))
    if active is True:
        stmt = stmt.where(Application.status.in_(ACTIVE_STATUSES))
    elif active is False:
        stmt = stmt.where(Application.status.not_in(ACTIVE_STATUSES))
    if track_id:
        stmt = stmt.where(Application.track_id == track_id)
    if company_id:
        stmt = stmt.where(Application.company_id == company_id)
    if season:
        rng = svc.season_range(season)
        if rng is None:
            raise HTTPException(status_code=422, detail="시즌 형식은 '2026 상반기' 처럼 써주세요")
        base = func.coalesce(
            Application.applied_at, Application.deadline_at, Application.discovered_at
        )
        stmt = stmt.where(base.between(rng[0], rng[1]))
    if deadline_from:
        stmt = stmt.where(Application.deadline_at >= deadline_from)
    if deadline_to:
        stmt = stmt.where(Application.deadline_at <= deadline_to)
    if event_from:
        stmt = stmt.where(Application.next_event_at >= event_from)
    if event_to:
        stmt = stmt.where(Application.next_event_at <= event_to)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(Application.title.ilike(like), Application.position.ilike(like)))

    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    col = SORTABLE[sort]
    stmt = stmt.order_by(
        col.asc().nulls_last() if order == "asc" else col.desc().nulls_last(),
        Application.created_at.desc(),
    )
    result = await db.execute(stmt.limit(limit).offset(offset))
    today = svc.today_kst()
    return ApplicationListOut(
        items=[ApplicationOut(**svc.to_out(a, today)) for a in result.scalars().all()], total=total
    )


@router.get("/stats", response_model=StatsOut)
async def stats(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> StatsOut:
    result = await db.execute(select(Application).where(Application.user_id == user_id))
    apps = list(result.scalars().all())

    by_status: dict[str, int] = {}
    seasons: dict[str, dict[str, int]] = {}
    tracks: dict[str, dict] = {}
    docs_stat: dict[str, dict] = {}
    funnel = {"applied": 0, "passed_docs": 0, "interview": 0, "offer": 0}

    def bump(bucket: dict[str, int], rank: int, is_offer: bool) -> None:
        bucket["total"] += 1
        if rank >= 2:
            bucket["applied"] += 1
        if rank >= 3:
            bucket["passed_docs"] += 1
        if rank >= 5:
            bucket["interview"] += 1
        if is_offer:
            bucket["offer"] += 1

    for a in apps:
        by_status[a.status] = by_status.get(a.status, 0) + 1
        rank = svc.reached_rank(a.status, a.end_stage)
        is_offer = a.status == "offer"
        if rank >= 2:
            funnel["applied"] += 1
        if rank >= 3:
            funnel["passed_docs"] += 1
        if rank >= 5:
            funnel["interview"] += 1
        if is_offer:
            funnel["offer"] += 1

        season = svc.season_of(a.applied_at, a.deadline_at, a.discovered_at) or "미정"
        bump(
            seasons.setdefault(
                season, {"total": 0, "applied": 0, "passed_docs": 0, "interview": 0, "offer": 0}
            ),
            rank,
            is_offer,
        )

        tkey = str(a.track_id) if a.track_id else "none"
        t = tracks.setdefault(
            tkey,
            {
                "track_id": a.track_id,
                "track_name": a.track.name if a.track else "트랙 없음",
                "total": 0,
                "applied": 0,
                "passed_docs": 0,
                "interview": 0,
                "offer": 0,
            },
        )
        bump(t, rank, is_offer)

        # 제출물 버전별 승률 — 자소서가 빠진 전형에서 "무엇을 냈나"를 가르는 축.
        # 한 지원에 여러 제출물이 붙으므로 합계는 지원 수보다 클 수 있다.
        for d in a.documents:
            entry = docs_stat.setdefault(
                str(d.id),
                {
                    "document_id": d.id,
                    "title": d.title,
                    "doc_type": d.doc_type,
                    "doc_type_label": DOC_TYPE_LABELS.get(d.doc_type, d.doc_type),
                    "total": 0,
                    "applied": 0,
                    "passed_docs": 0,
                    "interview": 0,
                    "offer": 0,
                },
            )
            bump(entry, rank, is_offer)

    return StatsOut(
        by_status=by_status,
        by_season=[SeasonStat(season=k, **v) for k, v in sorted(seasons.items(), reverse=True)],
        by_track=[
            TrackStat(**v)
            for v in sorted(tracks.values(), key=lambda x: (-x["total"], x["track_name"]))
        ],
        by_document=[
            DocumentStat(**v)
            for v in sorted(docs_stat.values(), key=lambda x: (-x["total"], x["title"]))
        ],
        funnel=funnel,
        active_count=sum(1 for a in apps if a.status in ACTIVE_STATUSES),
        total=len(apps),
    )


# ---------------------------------------------------------------- 생성 · 조회 · 수정 · 삭제
@router.post("", response_model=ApplicationOut, status_code=201)
async def create_application(
    body: ApplicationCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApplicationOut:
    cid, tid = await _resolve_refs(
        db,
        user_id,
        company_id=body.company_id,
        company_name=body.company_name,
        track_id=body.track_id,
        track_name=body.track_name,
    )
    docs = await _resolve_docs(db, user_id, body.documents)
    resume = await _resolve_doc(
        db, user_id, doc_id=body.resume_document_id, doc_title=body.resume_document_title
    )
    if resume and all(d.id != resume.id for d in docs):
        docs.append(resume)
    assert cid is not None
    company = await svc_owned(db, user_id, "companies", cid)
    try:
        end_stage = svc.validate_status_change(
            body.status.value, body.end_stage.value if body.end_stage else None
        )
    except svc.StatusChangeError as e:
        raise HTTPException(status_code=422, detail=str(e))

    today = svc.today_kst()
    app = Application(
        user_id=user_id,
        company_id=cid,
        track_id=tid,
        title=(body.title or svc.default_title(company.name, body.position)).strip(),
        position=body.position.strip(),
        posting_url=body.posting_url,
        status=body.status.value,
        end_stage=end_stage,
        employment_type=body.employment_type.value if body.employment_type else None,
        hiring_type=body.hiring_type.value if body.hiring_type else None,
        discovered_at=body.discovered_at or today,
        applied_at=body.applied_at or (today if body.status.value == "applied" else None),
        deadline_at=body.deadline_at,
        next_event_at=body.next_event_at,
        next_action=body.next_action,
        retrospective=body.retrospective,
        documents=docs,
    )
    db.add(app)
    try:
        await db.flush()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="같은 회사에 같은 제목의 지원이 이미 있어요")
    svc.record_history(db, app, None, app.status, source="user")
    await db.commit()
    app = await _get_owned(db, user_id, app.id)  # 관계(company 등) 로드된 상태로 재조회
    return ApplicationOut(**svc.to_out(app, today))


@router.get("/{app_id}", response_model=ApplicationDetailOut)
async def get_application(
    app_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApplicationDetailOut:
    app = await _get_owned(db, user_id, app_id)
    await db.refresh(app, attribute_names=["history"])
    return ApplicationDetailOut(**svc.to_out(app), history=app.history)  # type: ignore[arg-type]


@router.patch("/{app_id}", response_model=ApplicationOut)
async def update_application(
    app_id: uuid.UUID,
    body: ApplicationUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApplicationOut:
    app = await _get_owned(db, user_id, app_id)
    cid, tid = await _resolve_refs(
        db,
        user_id,
        company_id=body.company_id,
        company_name=body.company_name,
        track_id=body.track_id,
        track_name=body.track_name,
    )
    if cid:
        app.company_id = cid
    if tid:
        app.track_id = tid
    elif body.clear_track:
        app.track_id = None

    # 제출물: documents 는 집합 전체를 대체하고, resume_* 는 이력서 슬롯만 건드린다
    if body.documents is not None:
        svc.set_documents(app, await _resolve_docs(db, user_id, body.documents))
    elif body.clear_documents:
        svc.set_documents(app, [])
    resume = await _resolve_doc(
        db, user_id, doc_id=body.resume_document_id, doc_title=body.resume_document_title
    )
    if resume:
        svc.replace_resume(app, resume)
    elif body.clear_resume_document:
        svc.replace_resume(app, None)

    for name in (
        "position",
        "title",
        "posting_url",
        "discovered_at",
        "applied_at",
        "deadline_at",
        "next_event_at",
        "next_action",
        "retrospective",
    ):
        v = getattr(body, name)
        if v is not None:
            setattr(app, name, v.strip() if isinstance(v, str) else v)
    if body.employment_type is not None:
        app.employment_type = body.employment_type.value
    if body.hiring_type is not None:
        app.hiring_type = body.hiring_type.value
    await db.commit()
    app = await _get_owned(db, user_id, app_id)
    return ApplicationOut(**svc.to_out(app))


@router.patch("/{app_id}/status", response_model=StatusChangeOut)
async def change_status(
    app_id: uuid.UUID,
    body: StatusChange,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> StatusChangeOut:
    app = await _get_owned(db, user_id, app_id)
    try:
        celebration = svc.change_status(
            db,
            app,
            body.status.value,
            body.end_stage.value if body.end_stage else None,
            note=body.note,
            source="user",
        )
    except svc.StatusChangeError as e:
        raise HTTPException(status_code=422, detail=str(e))
    await db.commit()
    app = await _get_owned(db, user_id, app_id)
    return StatusChangeOut(application=ApplicationOut(**svc.to_out(app)), celebration=celebration)


@router.delete("/{app_id}", status_code=204)
async def delete_application(
    app_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    app = await _get_owned(db, user_id, app_id)
    await db.delete(app)
    await db.commit()


# ---------------------------------------------------------------- 제출물 연결
@router.post("/{app_id}/documents", response_model=ApplicationOut, status_code=201)
async def add_document(
    app_id: uuid.UUID,
    body: DocumentInput,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApplicationOut:
    """이 지원에 제출물을 하나 붙인다(이력서·포트폴리오·경험기술서 등)."""
    app = await _get_owned(db, user_id, app_id)
    doc = await _resolve_doc(db, user_id, doc_id=body.id, doc_title=body.title, doc_type=body.doc_type)
    if doc is None:
        raise HTTPException(status_code=422, detail="제출물은 id 나 제목 중 하나가 필요해요")
    svc.attach_document(app, doc)
    await db.commit()
    return ApplicationOut(**svc.to_out(await _get_owned(db, user_id, app_id)))


@router.delete("/{app_id}/documents/{doc_id}", response_model=ApplicationOut)
async def remove_document(
    app_id: uuid.UUID,
    doc_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ApplicationOut:
    """연결만 끊는다. 문서 자체는 남는다(다른 지원이 쓰고 있을 수 있다)."""
    app = await _get_owned(db, user_id, app_id)
    if not svc.detach_document(app, doc_id):
        raise HTTPException(status_code=404, detail="이 지원에 붙어 있지 않은 제출물이에요")
    await db.commit()
    return ApplicationOut(**svc.to_out(await _get_owned(db, user_id, app_id)))


# ---------------------------------------------------------------- 노션 CSV 임포트
@router.post("/import/notion-csv", response_model=ImportReport)
async def import_csv(
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="true 면 검증만 하고 저장하지 않음"),
    on_duplicate: Literal["skip", "update"] = Query("skip"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ImportReport:
    content = await file.read()
    try:
        report = await import_notion_csv(
            db, user_id, content, dry_run=dry_run, on_duplicate=on_duplicate
        )
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    if dry_run:
        await db.rollback()
    else:
        await db.commit()
    return ImportReport(**report)
