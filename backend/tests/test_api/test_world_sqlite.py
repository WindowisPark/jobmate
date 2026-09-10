"""월드 상태 API — 지원 데이터가 방의 신호로 나오는지, 말풍선 수락이 DM 에 남는지.

Redis 는 가짜로 대체한다. 메시지 저장까지 SQLite 에서 돈다
(Message 의 JSON 컬럼에 sqlite variant 를 둔 덕분).
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.middleware.auth import get_current_user_id
from app.dependencies import get_db, get_redis
from app.main import app
from app.models.agent_state import Agent
from app.models.application import (
    Application,
    ApplicationDocument,
    ApplicationStatusHistory,
    Company,
    Document,
    Track,
)
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import Base, User

USER_ID = uuid.uuid4()
TABLES = [
    User.__table__,
    Agent.__table__,
    Company.__table__,
    Track.__table__,
    Document.__table__,
    Application.__table__,
    ApplicationDocument.__table__,
    ApplicationStatusHistory.__table__,
    Conversation.__table__,
    Message.__table__,
]


class FakeRedis:
    """setex / get / mget 만 쓴다. TTL 은 검사하지 않는다."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def setex(self, key, ttl, value):
        self.store[key] = value

    async def get(self, key):
        return self.store.get(key)

    async def mget(self, keys):
        return [self.store.get(k) for k in keys]


@pytest.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=TABLES))
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as s:
        s.add(User(id=USER_ID, email="me@test.local", password_hash="x", nickname="나"))
        for aid, name in [("jun_ho", "탐색이"), ("ha_eun", "토닥이"), ("min_su", "꿀팁이"), ("seo_yeon", "첨삭이")]:
            s.add(Agent(id=aid, name=name, role="r", personality="p", avatar_url="/a.png"))
        await s.commit()

    redis = FakeRedis()

    async def _db():
        async with sessionmaker() as s:
            yield s

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    app.dependency_overrides[get_redis] = lambda: redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        c.redis = redis  # type: ignore[attr-defined]
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def _add(client, **over):
    body = {"company_name": "카카오", "position": "백엔드 개발자", "status": "applied"}
    body.update(over)
    r = await client.post("/api/applications", json=body)
    assert r.status_code == 201, r.text
    return r.json()


async def test_empty_room_is_quiet(client):
    state = (await client.get("/api/world/state")).json()
    assert state["npc_prompts"] == []
    tracker = next(b for b in state["buildings"] if b["id"] == "tracker")
    assert tracker["lit"] is False


async def test_urgent_deadline_lights_desk_and_makes_jun_ho_speak(client):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    await _add(client, deadline_at=tomorrow, resume_document_title="이력서 v3")

    state = (await client.get("/api/world/state")).json()

    tracker = next(b for b in state["buildings"] if b["id"] == "tracker")
    assert tracker["lit"] is True and tracker["label"] == "D-1"

    [p] = state["npc_prompts"]
    assert p["agent_id"] == "jun_ho"
    assert "카카오" in p["text"] and "이력서 v3" in p["text"]

    jun_ho = next(n for n in state["npcs"] if n["agent_id"] == "jun_ho")
    assert jun_ho["wants_to_talk"] is True


async def test_accept_writes_the_line_into_dm_without_llm(client):
    """수락하면 그 대사가 DM 에 에이전트 메시지로 남는다. 여기서 LLM 은 안 돈다."""
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    await _add(client, deadline_at=tomorrow, resume_document_title="이력서 v3")
    prompt = (await client.get("/api/world/state")).json()["npc_prompts"][0]

    r = await client.post(f"/api/world/prompts/{prompt['id']}/accept")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["room_id"] == "dm-jun_ho"
    assert body["suggested_reply"]

    # 그 방 대화에 실제로 한 줄이 들어갔는지 (라우트는 UUID 경로라 세션으로 확인)
    from sqlalchemy import select

    from app.services.chat_service import room_uuid

    gen = app.dependency_overrides[get_db]()
    db = await gen.__anext__()
    rows = (
        await db.execute(
            select(Message).where(Message.conversation_id == room_uuid("dm-jun_ho", USER_ID))
        )
    ).scalars().all()
    assert [m.content for m in rows] == [prompt["text"]]
    assert rows[0].sender_type == "agent" and rows[0].agent_id == "jun_ho"

    # 수락한 말풍선은 다시 뜨지 않는다
    assert (await client.get("/api/world/state")).json()["npc_prompts"] == []


async def test_dismiss_silences_until_tomorrow(client):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    await _add(client, deadline_at=tomorrow)
    prompt = (await client.get("/api/world/state")).json()["npc_prompts"][0]

    assert (await client.post(f"/api/world/prompts/{prompt['id']}/dismiss")).status_code == 204
    assert (await client.get("/api/world/state")).json()["npc_prompts"] == []


async def test_stale_prompt_id_is_404(client):
    r = await client.post("/api/world/prompts/deadline:gone:2026-01-01/accept")
    assert r.status_code == 404


async def test_celebration_can_be_acked(client):
    created = await _add(client, status="discovered")
    r = await client.patch(
        f"/api/applications/{created['id']}/status", json={"status": "offer"}
    )
    assert r.json()["celebration"] is True

    state = (await client.get("/api/world/state")).json()
    assert state["signals"]["celebration"] is not None
    # 붙은 직후에 "요즘 쉬고 있구나" 가 같이 뜨면 어긋난다
    assert [p["kind"] for p in state["npc_prompts"]] == ["celebration"]

    assert (
        await client.post(f"/api/world/celebrations/{created['id']}/ack")
    ).status_code == 204
    after = (await client.get("/api/world/state")).json()
    assert after["signals"]["celebration"] is None
    assert after["npc_prompts"] == []
