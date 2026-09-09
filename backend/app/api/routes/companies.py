"""회사·트랙·문서 — 지원 트래커의 참조 테이블 CRUD. 셋을 한 파일에 둔다(각 20줄 남짓)."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth import get_current_user_id
from app.dependencies import get_db
from app.models.application import Application, Company, Document, Track
from app.schemas.application import (
    CompanyCreate,
    CompanyOut,
    CompanyUpdate,
    DocumentCreate,
    DocumentOut,
    TrackCreate,
    TrackOut,
    TrackUpdate,
)

companies = APIRouter()
tracks = APIRouter()
documents = APIRouter()


async def _owned(db: AsyncSession, model, user_id: uuid.UUID, obj_id: uuid.UUID):
    result = await db.execute(select(model).where(model.id == obj_id, model.user_id == user_id))
    obj = result.scalar_one_or_none()
    if obj is None:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없어요")
    return obj


# ---------------------------------------------------------------- companies
@companies.get("", response_model=list[CompanyOut])
async def list_companies(
    q: str | None = Query(None, max_length=100),
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[CompanyOut]:
    stmt = (
        select(Company, func.count(Application.id))
        .outerjoin(Application, Application.company_id == Company.id)
        .where(Company.user_id == user_id)
        .group_by(Company.id)
        .order_by(Company.name)
    )
    if q:
        stmt = stmt.where(Company.name.ilike(f"%{q.strip()}%"))
    rows = (await db.execute(stmt)).all()
    return [CompanyOut.model_validate({**c.__dict__, "application_count": n}) for c, n in rows]


@companies.post("", response_model=CompanyOut, status_code=201)
async def create_company(
    body: CompanyCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> CompanyOut:
    dup = await db.scalar(
        select(Company).where(
            Company.user_id == user_id, func.lower(Company.name) == body.name.lower()
        )
    )
    if dup:
        raise HTTPException(status_code=409, detail="이미 있는 회사예요")
    c = Company(user_id=user_id, **body.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return CompanyOut.model_validate({**c.__dict__, "application_count": 0})


@companies.patch("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: uuid.UUID,
    body: CompanyUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> CompanyOut:
    c = await _owned(db, Company, user_id, company_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(c, k, v.strip() if isinstance(v, str) else v)
    await db.commit()
    await db.refresh(c)
    n = (
        await db.scalar(
            select(func.count()).select_from(Application).where(Application.company_id == c.id)
        )
        or 0
    )
    return CompanyOut.model_validate({**c.__dict__, "application_count": n})


@companies.delete("/{company_id}", status_code=204)
async def delete_company(
    company_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    c = await _owned(db, Company, user_id, company_id)
    n = (
        await db.scalar(
            select(func.count()).select_from(Application).where(Application.company_id == c.id)
        )
        or 0
    )
    if n:
        raise HTTPException(
            status_code=409, detail=f"이 회사에 지원 내역이 {n}건 있어 지울 수 없어요"
        )
    await db.delete(c)
    await db.commit()


# ---------------------------------------------------------------- tracks
@tracks.get("", response_model=list[TrackOut])
async def list_tracks(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[TrackOut]:
    rows = await db.execute(
        select(Track).where(Track.user_id == user_id).order_by(Track.sort_order, Track.name)
    )
    return [TrackOut.model_validate(t) for t in rows.scalars().all()]


@tracks.post("", response_model=TrackOut, status_code=201)
async def create_track(
    body: TrackCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TrackOut:
    dup = await db.scalar(
        select(Track).where(Track.user_id == user_id, func.lower(Track.name) == body.name.lower())
    )
    if dup:
        raise HTTPException(status_code=409, detail="이미 있는 트랙이에요")
    t = Track(user_id=user_id, **body.model_dump())
    db.add(t)
    await db.commit()
    await db.refresh(t)
    return TrackOut.model_validate(t)


@tracks.patch("/{track_id}", response_model=TrackOut)
async def update_track(
    track_id: uuid.UUID,
    body: TrackUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> TrackOut:
    t = await _owned(db, Track, user_id, track_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(t, k, v)
    await db.commit()
    await db.refresh(t)
    return TrackOut.model_validate(t)


@tracks.delete("/{track_id}", status_code=204)
async def delete_track(
    track_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    t = await _owned(db, Track, user_id, track_id)
    await db.delete(t)  # applications.track_id 는 SET NULL
    await db.commit()


# ---------------------------------------------------------------- documents (📚 건물의 stub)
@documents.get("", response_model=list[DocumentOut])
async def list_documents(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentOut]:
    rows = await db.execute(
        select(Document).where(Document.user_id == user_id).order_by(Document.updated_at.desc())
    )
    return [DocumentOut.model_validate(d) for d in rows.scalars().all()]


@documents.post("", response_model=DocumentOut, status_code=201)
async def create_document(
    body: DocumentCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> DocumentOut:
    dup = await db.scalar(
        select(Document).where(
            Document.user_id == user_id, func.lower(Document.title) == body.title.lower()
        )
    )
    if dup:
        raise HTTPException(status_code=409, detail="같은 제목의 문서가 이미 있어요")
    d = Document(user_id=user_id, **body.model_dump())
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return DocumentOut.model_validate(d)
