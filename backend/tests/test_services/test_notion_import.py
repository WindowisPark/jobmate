"""노션 CSV 정규화 — 파싱 규칙만(DB 없음)."""

from datetime import date, datetime

import pytest

from app.services import notion_import as ni


def test_first_relation_strips_notion_link_and_takes_first():
    assert (
        ni.first_relation(
            "백엔드 (https://www.notion.so/abc123), 데이터 (https://www.notion.so/def)"
        )
        == "백엔드"
    )
    assert ni.first_relation("카카오") == "카카오"
    assert ni.first_relation("") is None
    assert ni.first_relation(None) is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("2026-09-12", datetime(2026, 9, 12)),
        ("2026/09/12", datetime(2026, 9, 12)),
        ("September 12, 2026", datetime(2026, 9, 12)),
        ("September 12, 2026 3:00 PM", datetime(2026, 9, 12, 15, 0)),
        ("2026년 9월 12일", datetime(2026, 9, 12)),
        ("2026년 9월 12일 오후 3:00", datetime(2026, 9, 12, 15, 0)),
        ("September 1, 2026 → September 12, 2026", datetime(2026, 9, 1)),  # 범위는 시작일
        ("", None),
        (None, None),
    ],
)
def test_parse_notion_date(raw, expected):
    assert ni.parse_notion_date(raw, "마감일") == expected


def test_parse_notion_date_rejects_garbage():
    with pytest.raises(ni.RowError) as ei:
        ni.parse_notion_date("다음주쯤", "마감일")
    assert ei.value.field == "마감일"


def test_normalize_row_maps_korean_labels_to_keys():
    row = ni.normalize_row(
        {
            "제목": "카카오 - 백엔드 개발자",
            "회사": "카카오 (https://www.notion.so/xyz)",
            "포지션": "백엔드 개발자",
            "트랙": "백엔드",
            "상태": "코테·필기",
            "고용형태": "채용연계형 인턴",
            "채용방식": "수시",
            "마감일": "September 12, 2026",
            "지원일": "2026-09-01",
            "다음 일정": "September 15, 2026",
            "이력서 버전": "이력서 v3 (https://www.notion.so/doc)",
            "D-day": "3",
            "시즌": "2026 하반기",
        }
    )
    assert row.company_name == "카카오"
    assert row.status == "coding_test"
    assert row.employment_type == "intern_conversion"
    assert row.hiring_type == "rolling"
    assert row.track_name == "백엔드"
    assert row.deadline_at == date(2026, 9, 12)
    assert row.applied_at == date(2026, 9, 1)
    assert row.next_event_at == datetime(2026, 9, 15, 9, 0)  # 시간 없는 일정은 09:00
    assert row.resume_document_title == "이력서 v3"
    assert row.warnings == []


def test_normalize_row_recovers_company_from_title():
    row = ni.normalize_row({"제목": "네이버 - 프론트엔드", "회사": "", "포지션": ""})
    assert row.company_name == "네이버"
    assert row.position == "프론트엔드"
    assert row.title == "네이버 - 프론트엔드"


def test_normalize_row_builds_title_when_missing():
    row = ni.normalize_row({"제목": "", "회사": "라인", "포지션": "iOS"})
    assert row.title == "라인 - iOS"
    assert row.status == "discovered"  # 상태 빈값 → 발견


def test_normalize_row_drops_end_stage_for_open_status():
    row = ni.normalize_row({"회사": "쿠팡", "포지션": "데이터", "상태": "면접", "종료단계": "서류"})
    assert row.end_stage is None
    assert row.warnings and "종료단계" in row.warnings[0]


def test_normalize_row_keeps_end_stage_for_closed_status():
    row = ni.normalize_row({"회사": "쿠팡", "포지션": "데이터", "상태": "탈락", "종료단계": "코테"})
    assert row.status == "rejected"
    assert row.end_stage == "coding_test"


def test_normalize_row_errors():
    with pytest.raises(ni.RowError) as ei:
        ni.normalize_row({"회사": "", "포지션": "백엔드", "제목": "제목만"})
    assert ei.value.field == "회사"
    with pytest.raises(ni.RowError) as ei2:
        ni.normalize_row({"회사": "토스", "포지션": "백엔드", "상태": "합격대기"})
    assert "알 수 없는 상태" in ei2.value.reason


def test_read_csv_requires_headers_and_limits():
    headers, rows = ni.read_csv(
        "﻿제목,회사,포지션,상태\n카카오 - 백엔드,카카오,백엔드,지원완료\n".encode()
    )
    assert headers == ["제목", "회사", "포지션", "상태"]
    assert rows[0]["회사"] == "카카오"
    with pytest.raises(ValueError):
        ni.read_csv("이름,값\na,b\n".encode())


def test_dedupe_key_is_case_and_space_insensitive():
    assert ni.dedupe_key(" Kakao ", "Kakao - Backend") == ni.dedupe_key("kakao", "kakao - backend")
