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
from app.models.application import (
    Application,
    ApplicationDocument,
    ApplicationStatusHistory,
    Company,
    Document,
    Track,
)
from app.models.user import Base, User

USER_ID = uuid.uuid4()
OTHER_ID = uuid.uuid4()
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


async def test_multiple_documents_and_win_rate_by_document(client):
    """자소서를 빼고 이력서·포트폴리오·경험기술서를 함께 내는 전형 대응.

    지원 1건에 제출물 여러 개가 붙고, 통계는 제출물 버전별로 갈린다.
    """
    today = date.today()

    # 이력서 + 포트폴리오를 함께 낸 지원
    r = await client.post(
        "/api/applications",
        json={
            "company_name": "SK하이닉스",
            "position": "데이터 엔지니어",
            "status": "doc_passed",
            "resume_document_title": "이력서 v3",
            "documents": [{"title": "포트폴리오 v2", "doc_type": "portfolio"}],
        },
    )
    assert r.status_code == 201, r.text
    a1 = r.json()
    assert {d["title"] for d in a1["documents"]} == {"이력서 v3", "포트폴리오 v2"}
    # resume_document 는 이력서 종류에서 파생 — 기존 응답 모양이 유지된다
    assert a1["resume_document"]["title"] == "이력서 v3"
    assert a1["resume_document"]["doc_type_label"] == "이력서"

    # 경험기술서를 나중에 붙인다
    r = await client.post(
        f"/api/applications/{a1['id']}/documents",
        json={"title": "경험기술서 v1", "doc_type": "experience"},
    )
    assert r.status_code == 201, r.text
    assert len(r.json()["documents"]) == 3

    # 같은 이력서를 쓴 두 번째 지원 — 이쪽은 탈락
    r = await client.post(
        "/api/applications",
        json={
            "company_name": "한화생명",
            "position": "데이터 엔지니어",
            "status": "rejected",
            "end_stage": "document",
            "resume_document_title": "이력서 v3",
        },
    )
    assert r.status_code == 201, r.text

    # 제출물 버전별 승률: 이력서 v3 은 2건 중 1건 서류통과, 포트폴리오 v2 는 1건 중 1건
    stats = (await client.get("/api/applications/stats")).json()
    by_doc = {d["title"]: d for d in stats["by_document"]}
    assert by_doc["이력서 v3"]["total"] == 2 and by_doc["이력서 v3"]["passed_docs"] == 1
    assert by_doc["포트폴리오 v2"]["total"] == 1 and by_doc["포트폴리오 v2"]["passed_docs"] == 1
    assert by_doc["경험기술서 v1"]["doc_type_label"] == "경험기술서"

    # 이력서만 갈아끼운다 — 포트폴리오·경험기술서 연결은 그대로
    r = await client.patch(
        f"/api/applications/{a1['id']}", json={"resume_document_title": "이력서 v4"}
    )
    assert r.status_code == 200, r.text
    titles = {d["title"] for d in r.json()["documents"]}
    assert titles == {"이력서 v4", "포트폴리오 v2", "경험기술서 v1"}
    assert r.json()["resume_document"]["title"] == "이력서 v4"

    # 연결만 끊는다 — 문서 자체는 남아 다른 지원에서 계속 쓸 수 있다
    doc_id = next(d["id"] for d in r.json()["documents"] if d["title"] == "포트폴리오 v2")
    r = await client.delete(f"/api/applications/{a1['id']}/documents/{doc_id}")
    assert r.status_code == 200 and len(r.json()["documents"]) == 2
    assert any(d["title"] == "포트폴리오 v2" for d in (await client.get("/api/documents")).json())
    # 이미 끊긴 연결을 또 끊으면 404
    assert (await client.delete(f"/api/applications/{a1['id']}/documents/{doc_id}")).status_code == 404

    # documents 를 주면 집합 전체가 대체된다
    r = await client.patch(
        f"/api/applications/{a1['id']}",
        json={"documents": [{"title": "이력서 v4"}]},
    )
    assert [d["title"] for d in r.json()["documents"]] == ["이력서 v4"]
    assert today.year > 2000  # 날짜 고정 없이도 도는 흐름


async def test_stats_splits_by_hiring_type(client):
    """채용방식별로 갈라 봐야 오도하지 않는다.

    자소서가 빠진 수시 전형은 지원 비용이 낮아 건수가 늘고 통과율이 떨어진다.
    전체 평균만 보면 실력이 나빠진 것처럼 읽힌다.
    """
    for company, hiring, status in [
        ("공채회사A", "open_recruitment", "doc_passed"),
        ("공채회사B", "open_recruitment", "rejected"),
        ("수시회사A", "rolling", "rejected"),
        ("수시회사B", "rolling", "rejected"),
        ("수시회사C", "rolling", "rejected"),
    ]:
        body = {
            "company_name": company,
            "position": "백엔드",
            "status": status,
            "hiring_type": hiring,
        }
        if status == "rejected":
            body["end_stage"] = "document"
        r = await client.post("/api/applications", json=body)
        assert r.status_code == 201, r.text

    stats = (await client.get("/api/applications/stats")).json()
    by_hiring = {h["hiring_label"]: h for h in stats["by_hiring_type"]}

    assert by_hiring["공채"]["applied"] == 2 and by_hiring["공채"]["passed_docs"] == 1
    assert by_hiring["수시"]["applied"] == 3 and by_hiring["수시"]["passed_docs"] == 0
    # 전체로 뭉치면 5건 중 1건이라 수시가 공채를 끌어내린 것처럼 보인다
    assert stats["funnel"]["applied"] == 5 and stats["funnel"]["passed_docs"] == 1


async def test_stats_labels_missing_hiring_type(client):
    r = await client.post(
        "/api/applications", json={"company_name": "미지정회사", "position": "백엔드"}
    )
    assert r.status_code == 201
    stats = (await client.get("/api/applications/stats")).json()
    assert [h["hiring_label"] for h in stats["by_hiring_type"]] == ["미지정"]
