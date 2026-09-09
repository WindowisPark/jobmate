"""파생 필드·상태 규칙 — DB 없이 순수 함수만."""

from datetime import date

import pytest

from app.services import application_service as svc


def test_d_day_counts_from_today():
    today = date(2026, 9, 9)
    assert svc.d_day(date(2026, 9, 12), today) == 3
    assert svc.d_day(date(2026, 9, 9), today) == 0
    assert svc.d_day(date(2026, 9, 1), today) == -8
    assert svc.d_day(None, today) is None


def test_season_prefers_applied_then_deadline_then_discovered():
    assert svc.season_of(date(2026, 3, 1), date(2026, 9, 1), None) == "2026 상반기"
    assert svc.season_of(None, date(2026, 9, 1), None) == "2026 하반기"
    assert svc.season_of(None, None, date(2025, 12, 31)) == "2025 하반기"
    assert svc.season_of(None, None, None) is None


def test_season_range_parses_korean_halves():
    assert svc.season_range("2026 상반기") == (date(2026, 1, 1), date(2026, 6, 30))
    assert svc.season_range("2026 하반기") == (date(2026, 7, 1), date(2026, 12, 31))
    assert svc.season_range("2026") is None
    assert svc.season_range("상반기 2026") is None


@pytest.mark.parametrize(
    ("status", "end_stage", "rank"),
    [
        ("discovered", None, 0),
        ("applied", None, 2),
        ("doc_passed", None, 3),
        ("coding_test", None, 4),
        ("interview", None, 5),
        ("offer", None, 6),
        ("rejected", "document", 2),  # 서류 탈락 = 지원은 했음
        ("rejected", "coding_test", 3),  # 코테 탈락 = 서류는 통과
        ("rejected", "interview", 5),
        ("withdrawn", None, 2),  # 종료단계 없는 포기도 지원으로 본다
        ("no_response", None, 2),
    ],
)
def test_reached_rank(status, end_stage, rank):
    assert svc.reached_rank(status, end_stage) == rank


def test_closed_statuses_require_end_stage():
    with pytest.raises(svc.StatusChangeError):
        svc.validate_status_change("rejected", None)
    with pytest.raises(svc.StatusChangeError):
        svc.validate_status_change("withdrawn", None)
    assert svc.validate_status_change("rejected", "interview") == "interview"


def test_open_statuses_clear_end_stage():
    # 탈락에서 다시 진행으로 되돌리면 종료단계는 서버가 지운다
    assert svc.validate_status_change("applied", "document") is None
    assert svc.validate_status_change("offer", "final") is None


def test_default_title_is_company_dash_position():
    assert svc.default_title(" 카카오 ", "백엔드 개발자 ") == "카카오 - 백엔드 개발자"


def test_format_context_is_agent_specific():
    summary = {
        "total": 3,
        "active_count": 2,
        "urgent_deadlines": [
            {"company": "카카오", "position": "백엔드", "d_day": 1, "resume_document": "이력서 v3"}
        ],
        "next_event": None,
        "overdue": [],
        "rejection_streak_14d": 3,
        "celebration": None,
        "stage_counts": {"applied": 2, "rejected": 1},
    }
    jun = svc.format_application_context(summary, "jun_ho")
    ha = svc.format_application_context(summary, "ha_eun")
    assert "D-1" in jun and "이력서 v3" in jun
    assert "탈락 3건" in ha and "카카오" not in ha  # 멘탈 케어에는 마감 수치를 들이밀지 않는다
    assert svc.format_application_context({"total": 0}, "jun_ho") == ""
