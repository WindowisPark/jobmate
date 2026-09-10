"""Postgres·Redis 없이 백엔드를 띄운다 — 프런트 개발·UI 검증용.

    cd backend && python scripts/dev_sqlite.py            # http://localhost:8000

- DB: SQLite 파일(./dev-sqlite.db). 이식 가능한 테이블만 만든다(users, 트래커 5종, conversations).
  JSONB 를 쓰는 messages / job_* 테이블은 만들지 않으므로 **채팅·공고 검색은 동작하지 않는다**.
- Redis: 프로세스 메모리의 가짜 클라이언트(refresh token 저장용 set/get/delete 만).
- 인증: /api/auth/guest, /login, /register, /me, /refresh 전부 동작. 지원 트래커 API 전부 동작.
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("JOBMATE_DATABASE_URL", f"sqlite+aiosqlite:///{(ROOT / 'dev-sqlite.db').as_posix()}")
os.environ.setdefault("JOBMATE_DEBUG", "false")

from app import dependencies  # noqa: E402  (env 설정 뒤에 import 해야 engine 이 sqlite 로 만들어진다)


class FakeRedis:
    """auth·world 라우트가 쓰는 메서드만 흉내낸다. TTL 은 무시한다."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> None:  # noqa: ARG002
        self.store[key] = value

    async def get(self, key: str) -> str | None:
        return self.store.get(key)

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)

    async def setex(self, key: str, ttl: int, value: str) -> None:  # noqa: ARG002
        self.store[key] = value

    async def mget(self, keys: list[str]) -> list[str | None]:
        return [self.store.get(k) for k in keys]


dependencies.redis_client = FakeRedis()  # type: ignore[assignment]

from app.models.application import (  # noqa: E402
    Application, ApplicationDocument, ApplicationStatusHistory, Company, Document, Track,
)
from app.models.agent_state import Agent  # noqa: E402
from app.models.conversation import Conversation  # noqa: E402
from app.models.message import Message  # noqa: E402
from app.models.user import Base, User  # noqa: E402

TABLES = [
    User.__table__, Company.__table__, Track.__table__, Document.__table__,
    Application.__table__, ApplicationDocument.__table__,
    ApplicationStatusHistory.__table__, Agent.__table__,
    Conversation.__table__, Message.__table__,
]


async def init_db() -> None:
    async with dependencies.engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=TABLES))

    # messages.agent_id 가 agents 를 참조한다 — 말풍선 수락이 DM 에 메시지를 남기려면 필요
    from sqlalchemy import select

    from app.agents.profiles import AGENT_PROFILES

    async with dependencies.async_session() as db:
        existing = set((await db.execute(select(Agent.id))).scalars().all())
        for aid, prof in AGENT_PROFILES.items():
            if aid in existing:
                continue
            db.add(
                Agent(
                    id=aid,
                    name=prof["name"],
                    role=prof["role"],
                    personality=prof["personality"],
                    avatar_url=f"/room/pixel/blob_{aid}.png",
                )
            )
        await db.commit()


if __name__ == "__main__":
    asyncio.run(init_db())
    import uvicorn

    print(f"[dev_sqlite] DB = {os.environ['JOBMATE_DATABASE_URL']}  (채팅 LLM·공고검색 비활성)")
    uvicorn.run("app.main:app", host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), log_level="warning")
