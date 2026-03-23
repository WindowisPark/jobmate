from app.tools.search_jobs import search_jobs


async def test_search_jobs_returns_structure():
    result = await search_jobs(keywords=["백엔드", "Python"])
    assert "jobs" in result
    assert "total" in result
    assert isinstance(result["jobs"], list)
