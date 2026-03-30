"""직무 프리퍼런스 CRUD + 공고 갱신 API."""

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth import get_current_user_id, get_optional_user_id
from app.dependencies import get_db
from app.models.job_preference import JobPreference
from app.services.chat_service import ANONYMOUS_USER_ID, ensure_anonymous_user
from app.tools.search_jobs import search_jobs_with_preferences

router = APIRouter()


class JobPreferenceUpdate(BaseModel):
    job_field: str | None = None
    location: str | None = None
    career_level: str | None = None
    keywords: list[str] | None = None
    salary_min: int | None = None
    company_size: str | None = None


class JobPreferenceResponse(BaseModel):
    id: str
    job_field: str | None
    location: str | None
    career_level: str | None
    keywords: list[str]
    salary_min: int | None
    company_size: str | None
    is_active: bool


async def _resolve_user_id(
    user_id: UUID | None, db: AsyncSession
) -> UUID:
    """인증된 유저 또는 anonymous 유저 ID를 반환."""
    if user_id:
        return user_id
    return await ensure_anonymous_user(db)


@router.get("/preferences")
async def get_preferences(
    user_id: UUID | None = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    uid = await _resolve_user_id(user_id, db)
    result = await db.execute(
        select(JobPreference)
        .where(JobPreference.user_id == uid, JobPreference.is_active.is_(True))
        .order_by(JobPreference.updated_at.desc())
    )
    prefs = result.scalars().all()
    return {
        "preferences": [
            JobPreferenceResponse(
                id=str(p.id),
                job_field=p.job_field,
                location=p.location,
                career_level=p.career_level,
                keywords=p.keywords or [],
                salary_min=p.salary_min,
                company_size=p.company_size,
                is_active=p.is_active,
            ).model_dump()
            for p in prefs
        ]
    }


@router.put("/preferences")
async def update_preferences(
    body: JobPreferenceUpdate,
    user_id: UUID | None = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    uid = await _resolve_user_id(user_id, db)

    # 기존 활성 프리퍼런스 조회
    result = await db.execute(
        select(JobPreference)
        .where(JobPreference.user_id == uid, JobPreference.is_active.is_(True))
        .limit(1)
    )
    existing = result.scalar_one_or_none()

    if existing:
        if body.job_field is not None:
            existing.job_field = body.job_field
        if body.location is not None:
            existing.location = body.location
        if body.career_level is not None:
            existing.career_level = body.career_level
        if body.keywords is not None:
            existing.keywords = body.keywords
        if body.salary_min is not None:
            existing.salary_min = body.salary_min
        if body.company_size is not None:
            existing.company_size = body.company_size
    else:
        existing = JobPreference(
            user_id=uid,
            job_field=body.job_field,
            location=body.location,
            career_level=body.career_level,
            keywords=body.keywords or [],
            salary_min=body.salary_min,
            company_size=body.company_size,
        )
        db.add(existing)

    await db.commit()
    return {"status": "ok", "message": "직무 선호도가 저장되었습니다."}


@router.post("/refresh")
async def refresh_jobs(
    user_id: UUID | None = Depends(get_optional_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    uid = await _resolve_user_id(user_id, db)
    result = await search_jobs_with_preferences(
        db, str(uid), limit=10, force_refresh=True
    )
    await db.commit()
    return result
