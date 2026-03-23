import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def search_jobs(
    keywords: list[str],
    location: str | None = None,
    career_level: str = "신입",
    limit: int = 5,
) -> dict:
    """공공데이터포털 + 사람인 API에서 채용공고를 검색합니다."""
    jobs: list[dict] = []

    # 1. 공공데이터포털 워크넷 API
    if settings.public_data_api_key:
        try:
            worknet_jobs = await _search_worknet(keywords, location, limit)
            jobs.extend(worknet_jobs)
        except Exception as e:
            logger.warning(f"공공데이터포털 API 실패: {e}")

    # 2. 사람인 API (키가 있을 때만)
    if settings.saramin_api_key:
        try:
            saramin_jobs = await _search_saramin(keywords, location, career_level, limit)
            jobs.extend(saramin_jobs)
        except Exception as e:
            logger.warning(f"사람인 API 실패: {e}")

    # 3. API 모두 실패 시 Fallback
    if not jobs:
        return {
            "source": "fallback",
            "total": 3,
            "message": "현재 실시간 채용 정보를 가져올 수 없어서 일반적인 정보를 제공합니다.",
            "jobs": [
                {
                    "title": f"{' '.join(keywords)} 개발자",
                    "company": "여러 기업 채용 중",
                    "location": location or "서울",
                    "career": career_level,
                    "url": "https://www.saramin.co.kr",
                    "tip": "사람인, 원티드, 잡코리아에서 직접 검색해보세요!",
                },
            ],
        }

    return {
        "source": "api",
        "total": len(jobs),
        "jobs": jobs[:limit],
    }


async def _search_worknet(
    keywords: list[str], location: str | None, limit: int
) -> list[dict]:
    """공공데이터포털 워크넷 채용정보 API."""
    keyword = " ".join(keywords)
    url = "http://openapi.work.go.kr/opi/opi/opia/wantedApi.do"
    params = {
        "authKey": settings.public_data_api_key,
        "callTp": "L",
        "returnType": "XML",
        "keyword": keyword,
        "display": str(limit),
        "start": "1",
    }
    if location:
        params["region"] = location

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()

    # XML 간이 파싱 (외부 라이브러리 없이)
    import re
    text = resp.text
    jobs = []
    for match in re.finditer(r"<wanted>(.*?)</wanted>", text, re.DOTALL):
        block = match.group(1)
        title = _xml_tag(block, "wantedTitle")
        company = _xml_tag(block, "company")
        region = _xml_tag(block, "region")
        career = _xml_tag(block, "career")
        sal = _xml_tag(block, "sal")
        url = _xml_tag(block, "wantedInfoUrl")
        if title:
            jobs.append({
                "title": title,
                "company": company or "미공개",
                "location": region or "",
                "career": career or "",
                "salary": sal or "",
                "url": url or "",
                "source": "워크넷",
            })
    return jobs


async def _search_saramin(
    keywords: list[str], location: str | None, career_level: str, limit: int
) -> list[dict]:
    """사람인 Open API."""
    keyword = " ".join(keywords)
    url = "https://oapi.saramin.co.kr/guide/job-search"
    params = {
        "access-key": settings.saramin_api_key,
        "keywords": keyword,
        "count": str(limit),
    }
    if location:
        params["loc_cd"] = location

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    jobs = []
    for item in data.get("jobs", {}).get("job", []):
        pos = item.get("position", {})
        company = item.get("company", {}).get("detail", {}).get("name", "미공개")
        jobs.append({
            "title": pos.get("title", ""),
            "company": company,
            "location": pos.get("location", {}).get("name", ""),
            "career": pos.get("experience-level", {}).get("name", ""),
            "url": item.get("url", ""),
            "source": "사람인",
        })
    return jobs


def _xml_tag(block: str, tag: str) -> str:
    """간단한 XML 태그 값 추출."""
    import re
    m = re.search(rf"<{tag}>(.*?)</{tag}>", block, re.DOTALL)
    return m.group(1).strip() if m else ""
