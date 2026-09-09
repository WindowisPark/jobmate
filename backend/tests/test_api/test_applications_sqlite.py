"""지원 트래커 API 통합 테스트 — Postgres 없이 SQLite(aiosqlite)로 라우트 전체 흐름을 돈다.

트래커 모델은 이식 가능한 타입만 쓰므로 필요한 테이블만 create_all 한다(JSONB 를 쓰는 다른 테이블은 제외).
get_db / get_current_user_id 를 오버라이드해 인증·세션을 대체한다.
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.middleware.auth import get_current_user_id
from app.dependencies import get_db
from app.main import app
from app.models.application import Application, ApplicationStatusHistory, Company, Document, Track
from app.models.user import Base, User

USER_ID = uuid.uuid4()
OTHER_ID = uuid.uuid4()
TABLES = [
    User.__table__,
    Company.__table__,
    Track.__table__,
    Document.__table__,
    Application.__table__,
    ApplicationStatusHistory.__table__,
]


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
        s.add_all(
            [
                User(id=USER_ID, email="me@test.local", password_hash="x", nickname="나"),
                User(id=OTHER_ID, email="other@test.local", password_hash="x", nickname="남"),
            ]
        )
        await s.commit()

    current = {"user": USER_ID}

    async def _db():
        async with sessionmaker() as s:
            yield s

    async def _uid():
        return current["user"]

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user_id] = _uid
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        c.switch_user = lambda uid: current.__setitem__("user", uid)  # type: ignore[attr-defined]
        yield c
    app.dependency_overrides.clear()
    await engine.dispose()


async def test_create_list_status_stats_flow(client):
    today = date.today()
    r = await client.post(
        "/api/applications",
        json={
            "company_name": "카카오",
            "position": "백엔드 개발자",
            "track_name": "백엔드",
            "status": "applied",
            "deadline_at": (today + timedelta(days=2)).isoformat(),
            "resume_document_title": "이력서 v3",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["title"] == "카카오 - 백엔드 개발자"
    assert body["company"]["name"] == "카카오"
    assert body["track"]["name"] == "백엔드"
    assert body["resume_document"]["title"] == "이력서 v3"
    assert body["d_day"] == 2
    assert body["applied_at"] == today.isoformat()  # applied 로 만들면 지원일 자동
    assert body["is_applied"] is True and body["passed_docs"] is False
    app_id = body["id"]

    # 같은 회사·제목은 409
    r = await client.post(
        "/api/applications", json={"company_name": "카카오", "position": "백엔드 개발자"}
    )
    assert r.status_code == 409

    # 목록 · 진행중 필터 · 검색
    r = await client.get("/api/applications", params={"active": "true", "sort": "deadline_at"})
    assert r.status_code == 200 and r.json()["total"] == 1
    r = await client.get("/api/applications", params={"q": "백엔드"})
    assert r.json()["total"] == 1
    r = await client.get(
        "/api/applications",
        params={"season": f"{today.year} {'상반기' if today.month <= 6 else '하반기'}"},
    )
    assert r.json()["total"] == 1
    r = await client.get("/api/applications", params={"season": "이상한값"})
    assert r.status_code == 422

    # 탈락은 종료단계 필수
    r = await client.patch(f"/api/applications/{app_id}/status", json={"status": "rejected"})
    assert r.status_code == 422
    r = await client.patch(f"/api/applications/{app_id}/status", json={"status": "doc_passed"})
    assert r.status_code == 200 and r.json()["application"]["passed_docs"] is True
    r = await client.patch(
        f"/api/applications/{app_id}/status", json={"status": "offer", "note": "드디어"}
    )
    assert r.status_code == 200 and r.json()["celebration"] is True

    # 상세: 이력 3건(생성 + 전환 2)
    r = await client.get(f"/api/applications/{app_id}")
    hist = r.json()["history"]
    assert [h["to_status"] for h in hist] == ["applied", "doc_passed", "offer"]
    assert hist[-1]["note"] == "드디어"

    # 통계
    r = await client.get("/api/applications/stats")
    st = r.json()
    assert st["total"] == 1 and st["funnel"]["offer"] == 1 and st["by_status"]["offer"] == 1
    assert st["by_track"][0]["track_name"] == "백엔드"

    # 부분 수정 (상태는 못 바꿈)
    r = await client.patch(
        f"/api/applications/{app_id}", json={"next_action": "연봉 협상 준비", "clear_track": True}
    )
    assert (
        r.status_code == 200
        and r.json()["next_action"] == "연봉 협상 준비"
        and r.json()["track"] is None
    )

    # 회사 삭제는 지원이 있으면 409
    companies = (await client.get("/api/companies")).json()
    assert companies[0]["application_count"] == 1
    r = await client.delete(f"/api/companies/{companies[0]['id']}")
    assert r.status_code == 409

    # 삭제 후 회사 삭제 가능
    assert (await client.delete(f"/api/applications/{app_id}")).status_code == 204
    assert (await client.delete(f"/api/companies/{companies[0]['id']}")).status_code == 204


async def test_user_isolation(client):
    r = await client.post("/api/applications", json={"company_name": "네이버", "position": "FE"})
    app_id = r.json()["id"]
    client.switch_user(OTHER_ID)
    assert (await client.get("/api/applications")).json()["total"] == 0
    assert (await client.get(f"/api/applications/{app_id}")).status_code == 404
    assert (
        await client.patch(f"/api/applications/{app_id}/status", json={"status": "applied"})
    ).status_code == 404


async def test_notion_csv_import_dry_run_then_commit(client):
    csv = (
        "﻿제목,회사,포지션,트랙,상태,종료단계,고용형태,채용방식,마감일,지원일,다음 일정,다음 액션,이력서 버전,D-day,시즌\n"
        '카카오 - 백엔드,카카오 (https://www.notion.so/a1),백엔드,백엔드 (https://www.notion.so/t1),코테·필기,,정규직,수시,"September 12, 2026",2026-09-01,"September 15, 2026",코테 준비,이력서 v3,3,2026 하반기\n'
        ",토스,서버 개발자,백엔드,탈락,서류,정규직,공채,2026-08-20,2026-08-10,,,,,\n"
        "라인 - iOS,라인,iOS,,합격대기,,,,,,,,,,\n"
    ).encode()

    r = await client.post(
        "/api/applications/import/notion-csv",
        params={"dry_run": "true"},
        files={"file": ("지원.csv", csv, "text/csv")},
    )
    assert r.status_code == 200, r.text
    rep = r.json()
    assert rep["dry_run"] is True and rep["total_rows"] == 3
    assert rep["created"] == 2 and len(rep["errors"]) == 1
    assert rep["errors"][0]["row"] == 4 and "알 수 없는 상태" in rep["errors"][0]["reason"]
    assert rep["preview"][0]["status"] == "코테·필기"
    # dry-run 은 저장하지 않는다
    assert (await client.get("/api/applications")).json()["total"] == 0

    r = await client.post(
        "/api/applications/import/notion-csv",
        params={"dry_run": "false"},
        files={"file": ("지원.csv", csv, "text/csv")},
    )
    assert r.json()["created"] == 2
    items = (
        await client.get("/api/applications", params={"sort": "applied_at", "order": "desc"})
    ).json()["items"]
    assert [i["title"] for i in items] == ["카카오 - 백엔드", "토스 - 서버 개발자"]
    kakao = items[0]
    assert kakao["status"] == "coding_test" and kakao["track"]["name"] == "백엔드"
    assert kakao["deadline_at"] == "2026-09-12" and kakao["resume_document"]["title"] == "이력서 v3"
    toss = items[1]
    assert (
        toss["status"] == "rejected"
        and toss["end_stage"] == "document"
        and toss["passed_docs"] is False
    )

    # 재임포트: 기본은 skip, update 면 갱신
    r = await client.post(
        "/api/applications/import/notion-csv",
        params={"dry_run": "false"},
        files={"file": ("지원.csv", csv, "text/csv")},
    )
    assert r.json()["skipped"] == 2 and r.json()["created"] == 0
    csv2 = csv.replace("코테·필기".encode(), "면접".encode())
    r = await client.post(
        "/api/applications/import/notion-csv",
        params={"dry_run": "false", "on_duplicate": "update"},
        files={"file": ("지원.csv", csv2, "text/csv")},
    )
    assert r.json()["updated"] == 2
    detail = (await client.get(f"/api/applications/{kakao['id']}")).json()
    assert detail["status"] == "interview"
    assert all(h["source"] == "import" for h in detail["history"])

    # 임포트 이력은 '최근 결과' 신호에서 제외돼야 한다 (탈락 스트릭 오발 방지)
    from app.dependencies import get_db as _g  # noqa: F401
    from app.services.application_service import build_application_summary

    gen = app.dependency_overrides[get_db]()
    db = await gen.__anext__()
    summary = await build_application_summary(db, USER_ID)
    assert summary["total"] == 2 and summary["rejection_streak_14d"] == 0
    assert summary["urgent_deadlines"] == [] or all(
        a["d_day"] <= 3 for a in summary["urgent_deadlines"]
    )
