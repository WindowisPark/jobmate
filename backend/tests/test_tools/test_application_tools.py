"""트래커 도구 — 채팅에서 지원 현황을 읽고 고치는 경로.

SQLite 로 실제 세션을 만들어 돌린다. 세션 주입은 _tool_exec 가 하지만
여기서는 도구 자체의 계약을 고정한다.
"""

import importlib
import uuid
from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.models.application import (
    Application,
    ApplicationDocument,
    ApplicationStatusHistory,
    Company,
    Document,
    Track,
)
from app.models.user import Base, User

tools = importlib.import_module("app.tools.applications")

USER_ID = uuid.uuid4()
TABLES = [
    User.__table__,
    Company.__table__,
    Track.__table__,
    Document.__table__,
    Application.__table__,
    ApplicationDocument.__table__,
    ApplicationStatusHistory.__table__,
]


@pytest.fixture
async def db():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=TABLES))
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as s:
        s.add(User(id=USER_ID, email="me@t.local", password_hash="x", nickname="나"))
        await s.commit()
    async with sessionmaker() as s:
        yield s
    await engine.dispose()


async def make(db, company: str, *, status="applied", deadline=None, position="백엔드"):
    c = Company(user_id=USER_ID, name=company)
    db.add(c)
    await db.flush()
    a = Application(
        user_id=USER_ID,
        company_id=c.id,
        title=f"{company} - {position}",
        position=position,
        status=status,
        deadline_at=deadline,
    )
    db.add(a)
    await db.flush()
    return a


async def test_lists_and_counts_active(db):
    await make(db, "카카오")
    await make(db, "네이버", status="rejected")

    got = await tools.get_my_applications(db=db, user_id=str(USER_ID))

    assert got["total"] == 2 and got["active_count"] == 1
    assert "진행 중 1건" in got["summary_line"]
    assert {i["company"] for i in got["items"]} == {"카카오", "네이버"}


async def test_only_urgent_filters_by_deadline(db):
    await make(db, "급한곳", deadline=date.today() + timedelta(days=1))
    await make(db, "여유", deadline=date.today() + timedelta(days=30))

    got = await tools.get_my_applications(only_urgent=True, db=db, user_id=str(USER_ID))

    assert [i["company"] for i in got["items"]] == ["급한곳"]
    assert got["items"][0]["d_day"] == 1


async def test_query_narrows_by_company(db):
    await make(db, "카카오")
    await make(db, "네이버")
    got = await tools.get_my_applications(query="카카오", db=db, user_id=str(USER_ID))
    assert [i["company"] for i in got["items"]] == ["카카오"]


async def test_update_by_title_query(db):
    await make(db, "카카오")

    got = await tools.update_application_status(
        status="doc_passed", title_query="카카오", db=db, user_id=str(USER_ID)
    )

    assert got["status"] == "updated" and got["to_status"] == "doc_passed"
    assert got["status_label"] == "서류통과"
    assert "카카오" in got["message"]


async def test_rejection_requires_end_stage(db):
    """탈락은 어디서 끝났는지가 있어야 한다. 없으면 고치지 않고 되묻게 한다."""
    await make(db, "카카오")

    got = await tools.update_application_status(
        status="rejected", title_query="카카오", db=db, user_id=str(USER_ID)
    )

    assert "error" in got and got["needs_end_stage"] is True

    ok = await tools.update_application_status(
        status="rejected", end_stage="document", title_query="카카오", db=db, user_id=str(USER_ID)
    )
    assert ok["status"] == "updated"


async def test_ambiguous_match_asks_instead_of_guessing(db):
    await make(db, "카카오", position="백엔드")
    await make(db, "카카오페이", position="백엔드")

    got = await tools.update_application_status(
        status="doc_passed", title_query="카카오", db=db, user_id=str(USER_ID)
    )

    assert "ambiguous" in got and len(got["ambiguous"]) == 2
    assert "status" not in got  # 아무것도 안 바꿨다


async def test_offer_reports_celebration(db):
    await make(db, "카카오")
    got = await tools.update_application_status(
        status="offer", title_query="카카오", db=db, user_id=str(USER_ID)
    )
    assert got["celebration"] is True


async def test_missing_target_is_an_error(db):
    assert "error" in await tools.update_application_status(
        status="offer", db=db, user_id=str(USER_ID)
    )
    assert "error" in await tools.update_application_status(
        status="offer", title_query="없는회사", db=db, user_id=str(USER_ID)
    )


async def test_other_users_rows_are_invisible(db):
    await make(db, "카카오")
    got = await tools.get_my_applications(db=db, user_id=str(uuid.uuid4()))
    assert got["total"] == 0
