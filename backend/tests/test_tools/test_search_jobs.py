import importlib
from unittest.mock import AsyncMock

# app.tools 패키지가 같은 이름의 함수를 export 해서 모듈은 importlib 로 잡는다
sj = importlib.import_module("app.tools.search_jobs")


async def test_search_jobs_returns_structure(monkeypatch):
    fake_jobs = [
        {
            "title": "백엔드 개발자",
            "company": "테스트",
            "url": "https://example.com/1",
            "source": "wanted",
        }
    ]
    for name in ("_search_wanted", "_search_saramin"):
        if hasattr(sj, name):
            monkeypatch.setattr(sj, name, AsyncMock(return_value=fake_jobs))

    result = await sj.search_jobs(keywords=["백엔드", "Python"])
    assert "jobs" in result
    assert "total" in result
    assert isinstance(result["jobs"], list)
