"""채용공고 검색 — 사람인 공식 오픈 API + 캐시.

원티드 내부 API 호출과 사람인 검색 페이지 HTML 파싱은 걷어냈다.
둘 다 공개된 접근 경로가 아니었고, User-Agent 를 무작위로 돌려 차단을 피하는
코드까지 있어 단순 수집이 아니라 회피로 읽힐 여지가 컸다.
채용공고 DB 는 저작권법상 데이터베이스제작자 권리의 보호 대상이고
그 권리에는 영리 요건이 없다. 비영리 개인 프로젝트도 안전지대가 아니다.

이제 공식 오픈 API 로만 받는다. 키가 없으면 검색을 흉내내지 않고
직접 검색할 수 있는 링크를 돌려준다. 링크를 거는 것 자체는 문제가 없다.
키 발급: https://oapi.saramin.co.kr
"""

import hashlib
import json
import logging
from datetime import datetime, timedelta
from html import unescape
from urllib.parse import quote_plus

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 6

SARAMIN_API = "https://oapi.saramin.co.kr/job-search"
API_TIMEOUT = 12
MAX_COUNT = 110  # 오픈 API 한 번에 받을 수 있는 상한

# 우리가 누구인지 밝히는 고정 UA. 무작위 로테이션은 차단 회피로 읽힌다.
USER_AGENT = "JobMate/1.0 (+https://github.com/WindowisPark/jobmate)"


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json"}


# ---------------------------------------------------------------------------
# 캐시
# ---------------------------------------------------------------------------


def _build_query_hash(keywords: list[str], location: str | None, career_level: str) -> str:
    normalized = json.dumps(
        {"keywords": sorted(keywords), "location": location, "career_level": career_level},
        sort_keys=True,
    )
    return hashlib.sha256(normalized.encode()).hexdigest()


async def _get_cached_results(db: AsyncSession, query_hash: str) -> list[dict] | None:
    from app.models.job_cache import JobCache

    result = await db.execute(
        select(JobCache)
        .where(JobCache.query_hash == query_hash, JobCache.expires_at > datetime.utcnow())
        .order_by(JobCache.fetched_at.desc())
        .limit(1)
    )
    cached = result.scalar_one_or_none()
    if cached:
        return cached.results.get("jobs", [])
    return None


async def _save_cache(
    db: AsyncSession,
    query_hash: str,
    source: str,
    jobs: list[dict],
    user_id: str | None = None,
) -> None:
    import uuid as _uuid

    from app.models.job_cache import JobCache

    user_uuid = None
    if user_id and user_id != "anonymous":
        try:
            user_uuid = _uuid.UUID(user_id)
        except ValueError:
            pass

    cache_entry = JobCache(
        user_id=user_uuid,
        query_hash=query_hash,
        source=source,
        results={"jobs": jobs},
        fetched_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=CACHE_TTL_HOURS),
    )
    db.add(cache_entry)

    await db.execute(delete(JobCache).where(JobCache.expires_at <= datetime.utcnow()))


# ---------------------------------------------------------------------------
# 메인 검색 함수
# ---------------------------------------------------------------------------


async def search_jobs(
    keywords: list[str],
    location: str | None = None,
    career_level: str = "신입",
    limit: int = 5,
    *,
    db: AsyncSession | None = None,
    user_id: str | None = None,
    force_refresh: bool = False,
) -> dict:
    """채용공고를 검색합니다 (사람인 공식 오픈 API)."""
    query_hash = _build_query_hash(keywords, location, career_level)

    if db and not force_refresh:
        cached = await _get_cached_results(db, query_hash)
        if cached:
            return {"source": "cache", "total": len(cached), "jobs": cached[:limit]}

    if not settings.saramin_api_key:
        return _manual_search(keywords, location, "채용 API 키가 설정되어 있지 않아요")

    try:
        jobs = await _search_saramin_api(keywords, location, career_level, limit)
    except Exception as e:
        logger.warning("사람인 오픈 API 실패: %s", e)
        return _manual_search(keywords, location, "지금 채용 정보를 받아오지 못했어요")

    if not jobs:
        return _manual_search(keywords, location, "조건에 맞는 공고를 찾지 못했어요")

    if db:
        await _save_cache(db, query_hash, "saramin_api", jobs, user_id)

    return {"source": "saramin_api", "total": len(jobs), "jobs": jobs[:limit]}


def _manual_search(keywords: list[str], location: str | None, reason: str) -> dict:
    """검색을 못 할 때 지어내지 않는다. 직접 찾아갈 링크만 준다."""
    words = " ".join(k.strip() for k in keywords if k and k.strip()) or "개발자"
    query = quote_plus(f"{words} {location}".strip() if location else words)
    return {
        "source": "manual",
        "total": 0,
        "jobs": [],
        "message": f"{reason}. 아래에서 직접 찾아볼 수 있어요.",
        "search_links": [
            {
                "site": "사람인",
                "url": f"https://www.saramin.co.kr/zf_user/search?searchword={query}",
            },
            {"site": "원티드", "url": f"https://www.wanted.co.kr/search?query={query}"},
            {"site": "잡코리아", "url": f"https://www.jobkorea.co.kr/Search/?stext={query}"},
        ],
    }


async def search_jobs_with_preferences(
    db: AsyncSession,
    user_id: str,
    limit: int = 10,
    force_refresh: bool = False,
) -> dict:
    """사용자의 저장된 프리퍼런스 기반으로 채용공고를 검색한다."""
    import uuid as _uuid

    from app.models.job_preference import JobPreference

    try:
        user_uuid = _uuid.UUID(user_id)
    except ValueError:
        return {"source": "error", "total": 0, "jobs": [], "message": "유효하지 않은 사용자입니다."}

    result = await db.execute(
        select(JobPreference)
        .where(JobPreference.user_id == user_uuid, JobPreference.is_active.is_(True))
        .order_by(JobPreference.updated_at.desc())
        .limit(1)
    )
    pref = result.scalar_one_or_none()

    if not pref:
        return {
            "source": "no_preferences",
            "total": 0,
            "jobs": [],
            "message": "저장된 직무 선호도가 없습니다. 먼저 관심 직무를 알려주세요!",
        }

    keywords = list(pref.keywords or [])
    if pref.job_field and pref.job_field not in keywords:
        keywords.insert(0, pref.job_field)

    if not keywords:
        keywords = ["개발자"]

    return await search_jobs(
        keywords=keywords,
        location=pref.location,
        career_level=pref.career_level or "신입",
        limit=limit,
        db=db,
        user_id=user_id,
        force_refresh=force_refresh,
    )


async def save_job_preferences(
    user_id: str,
    job_field: str | None = None,
    location: str | None = None,
    career_level: str | None = None,
    keywords: list[str] | None = None,
    salary_min: int | None = None,
    company_size: str | None = None,
    *,
    db: AsyncSession | None = None,
) -> dict:
    """사용자의 직무 선호도를 저장/갱신한다."""
    if not db:
        return {"status": "error", "message": "DB 세션이 필요합니다."}

    import uuid as _uuid

    from sqlalchemy import update as sa_update

    from app.models.job_preference import JobPreference

    try:
        user_uuid = _uuid.UUID(user_id)
    except ValueError:
        return {"status": "error", "message": "유효하지 않은 사용자입니다."}

    result = await db.execute(
        select(JobPreference)
        .where(JobPreference.user_id == user_uuid, JobPreference.is_active.is_(True))
        .limit(1)
    )
    existing = result.scalar_one_or_none()

    if existing:
        updates = {}
        if job_field is not None:
            updates["job_field"] = job_field
        if location is not None:
            updates["location"] = location
        if career_level is not None:
            updates["career_level"] = career_level
        if keywords is not None:
            updates["keywords"] = keywords
        if salary_min is not None:
            updates["salary_min"] = salary_min
        if company_size is not None:
            updates["company_size"] = company_size

        if updates:
            updates["updated_at"] = datetime.utcnow()
            await db.execute(
                sa_update(JobPreference).where(JobPreference.id == existing.id).values(**updates)
            )

        return {
            "status": "updated",
            "message": "직무 선호도가 업데이트되었습니다.",
            "preferences": {
                "job_field": updates.get("job_field", existing.job_field),
                "location": updates.get("location", existing.location),
                "career_level": updates.get("career_level", existing.career_level),
                "keywords": updates.get("keywords", existing.keywords),
            },
        }
    else:
        pref = JobPreference(
            user_id=user_uuid,
            job_field=job_field,
            location=location,
            career_level=career_level,
            keywords=keywords or [],
            salary_min=salary_min,
            company_size=company_size,
        )
        db.add(pref)
        return {
            "status": "created",
            "message": "직무 선호도가 저장되었습니다.",
            "preferences": {
                "job_field": job_field,
                "location": location,
                "career_level": career_level,
                "keywords": keywords or [],
            },
        }


# ---------------------------------------------------------------------------
# 사람인 공식 오픈 API
# ---------------------------------------------------------------------------

# 신입 자리를 찾을 때 함께 볼 만한 경력 표기
_ENTRY_OK = ("신입", "무관", "경력무관")


async def _search_saramin_api(
    keywords: list[str],
    location: str | None,
    career_level: str,
    limit: int,
) -> list[dict]:
    """공식 오픈 API 로 공고를 받는다.

    지역·경력은 파라미터로 보내지 않고 받은 결과에서 고른다.
    코드 체계를 문서로 확인하기 전까지는 확실한 파라미터만 보내는 편이 안전하다.
    그래서 넉넉히 받아 두고 여기서 좁힌다.
    """
    words = " ".join(k.strip() for k in keywords if k and k.strip())
    if not words:
        return []

    want = limit * 3 if (location or career_level) else limit
    params = {
        "access-key": settings.saramin_api_key,
        "keywords": words,
        "count": max(1, min(want, MAX_COUNT)),
        "start": 0,
        "fields": "posting-date+expiration-date",
    }

    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        resp = await client.get(SARAMIN_API, params=params, headers=_headers())
        resp.raise_for_status()
        data = resp.json()

    raw = (data.get("jobs") or {}).get("job") or []
    if isinstance(raw, dict):  # 결과가 하나면 배열이 아닐 수 있다
        raw = [raw]

    jobs = [j for j in (_parse_job(item) for item in raw) if j]

    if location:
        jobs = _prefer(jobs, lambda j: location in j["location"])
    if career_level == "신입":
        jobs = _prefer(jobs, lambda j: any(w in j["career"] for w in _ENTRY_OK))

    return jobs


def _prefer(jobs: list[dict], match) -> list[dict]:
    """조건에 맞는 것만 남기되, 하나도 안 남으면 원래 목록을 준다.

    빈손으로 돌려주면 에이전트가 "없다" 고 단정한다. 좁히다 지우는 것보다 낫다.
    """
    picked = [j for j in jobs if match(j)]
    return picked or jobs


def _clean(value: str | None) -> str:
    """오픈 API 는 HTML 이스케이프된 문자열을 준다. 지역은 '서울 &gt; 강남구' 꼴."""
    if not value:
        return ""
    return " ".join(unescape(value).replace(">", " ").split())


def _career_text(level: dict) -> str:
    """경력 표기. 보통 name 이 오지만(예: "경력 2~3년") 없을 때를 대비해 min·max 로 만든다."""
    name = _clean(level.get("name"))
    if name:
        return name
    lo, hi = level.get("min"), level.get("max")
    if lo in (None, "") and hi in (None, ""):
        return ""
    lo, hi = int(lo or 0), int(hi or 0)
    if lo == 0 and hi == 0:
        return "신입"
    if hi > lo:
        return f"경력 {lo}~{hi}년"
    return f"경력 {lo}년 이상"


def _deadline(item: dict) -> str:
    """마감일. expiration-date 는 fields 로 요청해야 오므로 timestamp 로 폴백한다."""
    value = item.get("expiration-date")
    if value:
        return str(value)
    ts = item.get("expiration-timestamp")
    if not ts:
        return ""
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d")
    except (ValueError, OSError, OverflowError):
        return ""


def _parse_job(item: dict) -> dict | None:
    position = item.get("position") or {}
    title = _clean(position.get("title"))
    if not title:
        return None

    def field(key: str) -> str:
        return _clean((position.get(key) or {}).get("name"))

    return {
        "title": title,
        "company": _clean(((item.get("company") or {}).get("detail") or {}).get("name"))
        or "미공개",
        "location": field("location"),
        "career": _career_text(position.get("experience-level") or {}),
        "education": field("required-education-level"),
        "employment_type": field("job-type"),
        "salary": _clean((item.get("salary") or {}).get("name")),
        "deadline": _deadline(item),
        "url": item.get("url") or "",
        "source": "saramin_api",
    }
