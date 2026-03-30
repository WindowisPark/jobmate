"""채용공고 검색 — 원티드 + 사람인 스크래핑 + 캐시."""

import hashlib
import json
import logging
import random
import re
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 6

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
]


def _random_headers() -> dict[str, str]:
    return {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "application/json, text/html, */*",
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        "Referer": "https://www.wanted.co.kr/",
    }


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

    await db.execute(
        delete(JobCache).where(JobCache.expires_at <= datetime.utcnow())
    )


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
    """채용공고를 검색합니다 (원티드 + 사람인 스크래핑)."""
    query_hash = _build_query_hash(keywords, location, career_level)

    # 캐시 확인
    if db and not force_refresh:
        cached = await _get_cached_results(db, query_hash)
        if cached:
            return {"source": "cache", "total": len(cached), "jobs": cached[:limit]}

    jobs: list[dict] = []

    # 1. 원티드 (JSON API — 주력)
    try:
        wanted_jobs = await _search_wanted(keywords, location, career_level, limit)
        jobs.extend(wanted_jobs)
    except Exception as e:
        logger.warning(f"원티드 스크래핑 실패: {e}")

    # 2. 사람인 (HTML 스크래핑 — 보조)
    if len(jobs) < limit:
        try:
            saramin_jobs = await _search_saramin(keywords, location, career_level, limit - len(jobs))
            jobs.extend(saramin_jobs)
        except Exception as e:
            logger.warning(f"사람인 스크래핑 실패: {e}")

    # 3. 모두 실패 시 Fallback
    if not jobs:
        return {
            "source": "fallback",
            "total": 1,
            "message": "현재 실시간 채용 정보를 가져올 수 없어서 일반적인 정보를 제공합니다.",
            "jobs": [
                {
                    "title": f"{' '.join(keywords)} 관련 채용",
                    "company": "여러 기업 채용 중",
                    "location": location or "서울",
                    "career": career_level,
                    "url": "https://www.wanted.co.kr",
                    "tip": "원티드, 사람인, 잡코리아에서 직접 검색해보세요!",
                },
            ],
        }

    # 캐시 저장
    if db:
        source = jobs[0].get("source", "scraping") if jobs else "scraping"
        await _save_cache(db, query_hash, source, jobs, user_id)

    return {"source": "scraping", "total": len(jobs), "jobs": jobs[:limit]}


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
                sa_update(JobPreference)
                .where(JobPreference.id == existing.id)
                .values(**updates)
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
# 원티드 스크래핑 (프론트엔드 JSON API)
# ---------------------------------------------------------------------------

# 원티드 경력 코드
_WANTED_YEARS = {"신입": 0, "경력 1-3년": 1, "경력 3-5년": 3, "무관": -1}

# 원티드 지역 코드 (tag_type_id=518)
_WANTED_LOCATIONS: dict[str, str] = {
    "서울": "seoul",
    "경기": "gyeonggi",
    "인천": "incheon",
    "부산": "busan",
    "대구": "daegu",
    "대전": "daejeon",
    "광주": "gwangju",
    "울산": "ulsan",
    "세종": "sejong",
    "강원": "gangwon",
    "경남": "gyeongnam",
    "경북": "gyeongbuk",
    "전남": "jeonnam",
    "전북": "jeonbuk",
    "충남": "chungnam",
    "충북": "chungbuk",
    "제주": "jeju",
    "판교": "gyeonggi",
}


async def _search_wanted(
    keywords: list[str],
    location: str | None,
    career_level: str,
    limit: int,
) -> list[dict]:
    """원티드 프론트엔드 API에서 채용공고를 검색한다."""
    keyword = " ".join(keywords)
    params: dict[str, str | int] = {
        "1": 518,  # tag_type_id for 개발
        "country": "kr",
        "job_sort": "job.latest_order",
        "locations": "all",
        "limit": min(limit, 20),
        "offset": 0,
    }

    # 경력 필터
    years = _WANTED_YEARS.get(career_level, -1)
    if years >= 0:
        params["years"] = years

    # 지역 필터
    if location:
        loc_code = _WANTED_LOCATIONS.get(location)
        if loc_code:
            params["locations"] = loc_code

    headers = _random_headers()
    headers["Referer"] = f"https://www.wanted.co.kr/search?query={keyword}&tab=position"

    async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
        # 원티드 검색 API
        resp = await client.get(
            "https://www.wanted.co.kr/api/v4/jobs",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    jobs = []
    for item in data.get("data", []):
        company = item.get("company", {})
        title = item.get("position", "")
        company_name = company.get("name", "미공개")
        job_location = item.get("address", {}).get("full_location", "")

        # 키워드 매칭 (원티드는 태그 기반이라 keyword 필터가 정확하지 않을 수 있음)
        if not _keyword_matches(keyword, title, company_name):
            continue

        reward = item.get("reward", {})
        reward_text = ""
        if reward.get("formatted_total"):
            reward_text = f"추천보상금 {reward['formatted_total']}"

        jobs.append({
            "title": title,
            "company": company_name,
            "location": job_location or "",
            "career": career_level,
            "salary": reward_text,
            "url": f"https://www.wanted.co.kr/wd/{item.get('id', '')}",
            "source": "원티드",
            "logo": company.get("application_response_stats", {}).get("avg_rate", ""),
        })

        if len(jobs) >= limit:
            break

    # 키워드 매칭이 너무 엄격하면 그냥 모두 반환
    if not jobs and data.get("data"):
        for item in data["data"][:limit]:
            company = item.get("company", {})
            jobs.append({
                "title": item.get("position", ""),
                "company": company.get("name", "미공개"),
                "location": item.get("address", {}).get("full_location", ""),
                "career": career_level,
                "salary": "",
                "url": f"https://www.wanted.co.kr/wd/{item.get('id', '')}",
                "source": "원티드",
            })

    return jobs


def _keyword_matches(keyword: str, title: str, company: str) -> bool:
    """키워드가 제목이나 회사명에 부분 매칭되는지 확인."""
    kw_lower = keyword.lower()
    target = f"{title} {company}".lower()
    # 키워드의 각 단어 중 하나라도 매칭되면 OK
    for word in kw_lower.split():
        if word in target:
            return True
    return False


# ---------------------------------------------------------------------------
# 사람인 스크래핑 (HTML)
# ---------------------------------------------------------------------------

_SARAMIN_CAREER = {"신입": 1, "경력 1-3년": 2, "경력 3-5년": 2, "무관": 0}


async def _search_saramin(
    keywords: list[str],
    location: str | None,
    career_level: str,
    limit: int,
) -> list[dict]:
    """사람인 검색 페이지를 스크래핑한다."""
    keyword = " ".join(keywords)
    params: dict[str, str | int] = {
        "searchType": "search",
        "searchword": keyword,
        "recruitPage": 1,
        "recruitSort": "relation",
        "recruitPageCount": min(limit, 40),
    }

    career_code = _SARAMIN_CAREER.get(career_level)
    if career_code:
        params["career"] = career_code

    headers = _random_headers()
    headers["Referer"] = "https://www.saramin.co.kr/"

    async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
        resp = await client.get(
            "https://www.saramin.co.kr/zf_user/search/recruit",
            params=params,
            headers=headers,
        )
        resp.raise_for_status()

    html = resp.text
    jobs = []

    # 사람인 검색 결과에서 채용공고 추출
    # 각 공고는 class="item_recruit" 내부에 있음
    for match in re.finditer(
        r'<div[^>]*class="item_recruit"[^>]*>(.*?)</div>\s*</div>\s*</div>',
        html,
        re.DOTALL,
    ):
        block = match.group(1)

        # 제목
        title_m = re.search(r'class="job_tit"[^>]*>.*?<a[^>]*>(.*?)</a>', block, re.DOTALL)
        title = _strip_html(title_m.group(1)) if title_m else ""

        # 회사명
        corp_m = re.search(r'class="corp_name"[^>]*>.*?<a[^>]*>(.*?)</a>', block, re.DOTALL)
        company = _strip_html(corp_m.group(1)) if corp_m else ""

        # URL
        link_m = re.search(r'<a[^>]*href="(/zf_user/jobs/relay/view[^"]*)"', block)
        url = f"https://www.saramin.co.kr{link_m.group(1)}" if link_m else ""

        # 조건 (지역, 경력, 학력, 고용형태)
        conditions = []
        for cond_m in re.finditer(r'<span[^>]*>(.*?)</span>', block):
            text = _strip_html(cond_m.group(1)).strip()
            if text and len(text) < 30:
                conditions.append(text)

        if title:
            jobs.append({
                "title": title,
                "company": company or "미공개",
                "location": conditions[0] if conditions else "",
                "career": conditions[1] if len(conditions) > 1 else "",
                "salary": "",
                "url": url,
                "source": "사람인",
            })

        if len(jobs) >= limit:
            break

    return jobs


def _strip_html(text: str) -> str:
    """HTML 태그 제거 및 공백 정리."""
    cleaned = re.sub(r"<[^>]+>", "", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def _xml_tag(block: str, tag: str) -> str:
    """간단한 XML 태그 값 추출."""
    m = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.DOTALL)
    return m.group(1).strip() if m else ""
