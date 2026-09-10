"""공용 도구 실행기 — DB 세션 주입 결함의 회귀 방지.

결함: 탐색이 노드만 user_id 를 주입하고 db 세션은 빠뜨려
save_job_preferences 가 항상 실패하고 공고 캐시가 저장되지 않았다.
나머지 세 노드는 주입 자체가 없어 DB 도구를 붙이는 순간 같은 자리에서 터졌다.
"""

import importlib

import pytest

tool_exec = importlib.import_module("app.agents.nodes._tool_exec")


class _FakeSession:
    def __init__(self, log: list[str]) -> None:
        self._log = log

    async def __aenter__(self) -> "_FakeSession":
        self._log.append("open")
        return self

    async def __aexit__(self, *exc) -> bool:
        self._log.append("close")
        return False

    async def commit(self) -> None:
        self._log.append("commit")


@pytest.fixture
def patched(monkeypatch):
    """ALL_TOOLS 와 세션 팩토리를 가짜로 바꾼다."""
    log: list[str] = []
    seen: dict = {}

    async def fake_db_tool(**kwargs):
        seen.update(kwargs)
        return {"ok": True}

    async def fake_plain_tool(**kwargs):
        seen.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(
        tool_exec,
        "ALL_TOOLS",
        {"save_job_preferences": fake_db_tool, "breathing_exercise": fake_plain_tool},
    )
    monkeypatch.setattr(tool_exec, "async_session", lambda: _FakeSession(log))
    return log, seen


async def test_db_tool_gets_session_and_commits(patched):
    log, seen = patched
    run = tool_exec.make_tool_executor("user-1")

    result = await run("save_job_preferences", {"job_field": "백엔드"})

    assert result == {"ok": True}
    assert seen["user_id"] == "user-1"
    assert seen["db"] is not None  # 결함의 핵심 — 세션이 실제로 넘어간다
    assert seen["job_field"] == "백엔드"
    # 캐시·선호 저장은 도구가 commit 하지 않으므로 실행기가 해야 한다
    assert log == ["open", "commit", "close"]


async def test_model_supplied_server_args_are_ignored(patched):
    """LLM 이 user_id 를 지어내 보내도 서버 값이 이긴다(중복 인자 TypeError 방지)."""
    _, seen = patched
    run = tool_exec.make_tool_executor("real-user")

    await run("save_job_preferences", {"user_id": "spoofed", "db": "junk", "location": "서울"})

    assert seen["user_id"] == "real-user"
    assert seen["db"] != "junk"
    assert seen["location"] == "서울"


async def test_plain_tool_opens_no_session(patched):
    log, seen = patched
    run = tool_exec.make_tool_executor("user-1")

    await run("breathing_exercise", {"duration": 60})

    assert log == []  # 세션이 필요 없는 도구는 커넥션을 잡지 않는다
    assert "db" not in seen and "user_id" not in seen


async def test_unknown_tool_returns_error(patched):
    run = tool_exec.make_tool_executor("user-1")
    assert "error" in await run("nope", {})


async def test_db_tool_without_login_is_refused(patched):
    log, _ = patched
    run = tool_exec.make_tool_executor("")
    result = await run("save_job_preferences", {})
    assert "error" in result
    assert log == []  # 세션도 열지 않는다
