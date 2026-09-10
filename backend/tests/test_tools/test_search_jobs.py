"""채용공고 검색 — 공식 오픈 API 경로와 키 없을 때의 처리.

스크래핑을 걷어낸 뒤의 계약을 고정한다. 네트워크는 타지 않는다.
"""

import importlib

import pytest

# app.tools 패키지가 같은 이름의 함수를 export 해서 모듈은 importlib 로 잡는다
sj = importlib.import_module("app.tools.search_jobs")


def _api_payload(jobs: list[dict]) -> dict:
    return {"jobs": {"count": len(jobs), "start": 0, "total": str(len(jobs)), "job": jobs}}


def _job(title="백엔드 개발자", company="테스트컴퍼니", loc="서울 &gt; 강남구", career="신입") -> dict:
    return {
        "url": "https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx=1",
        "company": {"detail": {"name": company}},
        "position": {
            "title": title,
            "location": {"name": loc},
            "experience-level": {"name": career},
            "required-education-level": {"name": "대학교졸업(4년)이상"},
            "job-type": {"name": "정규직"},
        },
        "salary": {"name": "회사내규에 따름"},
        "expiration-date": "2026-10-01T23:59:59+09:00",
    }


@pytest.fixture
def api(monkeypatch):
    """오픈 API 응답을 갈아끼우는 픽스처. 실제 HTTP 는 안 나간다."""
    state: dict = {"payload": _api_payload([_job()]), "calls": []}

    class _Resp:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return state["payload"]

    class _Client:
        def __init__(self, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, url, params=None, headers=None):
            state["calls"].append({"url": url, "params": params, "headers": headers})
            return _Resp()

    monkeypatch.setattr(sj.httpx, "AsyncClient", _Client)
    monkeypatch.setattr(sj.settings, "saramin_api_key", "test-key")
    return state


async def test_no_api_key_returns_links_not_fake_jobs(monkeypatch):
    """키가 없으면 공고를 지어내지 않는다. 예전 fallback 은 가짜 공고를 만들어 냈다."""
    monkeypatch.setattr(sj.settings, "saramin_api_key", "")

    result = await sj.search_jobs(keywords=["백엔드", "Python"])

    assert result["source"] == "manual"
    assert result["jobs"] == []
    assert [link["site"] for link in result["search_links"]] == ["사람인", "원티드", "잡코리아"]
    assert "%EB%B0%B1%EC%97%94%EB%93%9C" in result["search_links"][0]["url"]  # 백엔드 URL 인코딩


async def test_official_api_is_called_with_identifying_ua(api):
    result = await sj.search_jobs(keywords=["백엔드"], limit=5)

    call = api["calls"][0]
    assert call["url"] == sj.SARAMIN_API
    assert call["params"]["access-key"] == "test-key"
    assert call["params"]["keywords"] == "백엔드"
    # 우리가 누구인지 밝힌다. 무작위 UA 로테이션은 제거했다.
    assert call["headers"]["User-Agent"].startswith("JobMate/")
    assert result["source"] == "saramin_api"


async def test_parsed_job_shape(api):
    result = await sj.search_jobs(keywords=["백엔드"])
    job = result["jobs"][0]

    assert job["title"] == "백엔드 개발자"
    assert job["company"] == "테스트컴퍼니"
    assert job["location"] == "서울 강남구"  # &gt; 를 풀고 정리한다
    assert job["career"] == "신입"
    assert job["url"].startswith("https://www.saramin.co.kr/")
    assert job["source"] == "saramin_api"


async def test_location_filter_falls_back_instead_of_emptying(api):
    """지역으로 좁혀 아무것도 안 남으면 빈손 대신 원래 목록을 준다."""
    api["payload"] = _api_payload([_job(loc="부산 &gt; 해운대구")])

    result = await sj.search_jobs(keywords=["백엔드"], location="서울")

    assert result["total"] == 1
    assert result["jobs"][0]["location"] == "부산 해운대구"


async def test_single_job_object_is_accepted(api):
    """결과가 하나면 배열이 아니라 객체로 오는 경우가 있다."""
    api["payload"] = {"jobs": {"job": _job(title="데이터 엔지니어")}}

    result = await sj.search_jobs(keywords=["데이터"])

    assert result["total"] == 1 and result["jobs"][0]["title"] == "데이터 엔지니어"


async def test_api_failure_degrades_to_links(api, monkeypatch):
    class _Boom:
        def __init__(self, **kw):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *exc):
            return False

        async def get(self, *a, **kw):
            raise RuntimeError("503")

    monkeypatch.setattr(sj.httpx, "AsyncClient", _Boom)

    result = await sj.search_jobs(keywords=["백엔드"])

    assert result["source"] == "manual" and result["jobs"] == []
    assert result["search_links"]


async def test_empty_result_degrades_to_links(api):
    api["payload"] = _api_payload([])
    result = await sj.search_jobs(keywords=["백엔드"])
    assert result["source"] == "manual" and result["jobs"] == []
