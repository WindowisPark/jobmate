"""NPC 선제 대사 — 템플릿 규칙. LLM 도 DB 도 타지 않는 순수 함수다."""

import importlib
from datetime import datetime, timedelta

npc = importlib.import_module("app.services.npc_prompt_service")


def summary(**over) -> dict:
    base = {
        "today": "2026-09-10",
        "total": 5,
        "active_count": 3,
        "stage_counts": {"applied": 3},
        "urgent_deadlines": [],
        "overdue": [],
        "next_event": None,
        "recent_outcomes": [],
        "rejection_streak_14d": 0,
        "celebration": None,
    }
    base.update(over)
    return base


def app_brief(**over) -> dict:
    base = {
        "application_id": "a1",
        "title": "카카오 - 백엔드",
        "company": "카카오",
        "position": "백엔드",
        "status": "applied",
        "status_label": "지원완료",
        "deadline_at": "2026-09-11",
        "d_day": 1,
        "next_event_at": None,
        "next_action": None,
        "resume_document": "이력서 v3",
    }
    base.update(over)
    return base


def test_deadline_prompt_names_the_resume():
    """탐색이는 데이터를 알고 말을 건다. 막연한 응원이 아니라 이력서 버전을 짚는다."""
    [p] = npc.build_npc_prompts(summary(urgent_deadlines=[app_brief()]))

    assert p["agent_id"] == "jun_ho" and p["kind"] == "deadline"
    assert "카카오" in p["text"] and "내일" in p["text"] and "이력서 v3" in p["text"]
    assert p["suggested_reply"]


def test_deadline_without_resume_asks_to_pick_one():
    [p] = npc.build_npc_prompts(summary(urgent_deadlines=[app_brief(resume_document=None)]))
    assert "아직 안 골랐어" in p["text"]


def test_today_deadline_says_today():
    [p] = npc.build_npc_prompts(summary(urgent_deadlines=[app_brief(d_day=0)]))
    assert "오늘" in p["text"]


def test_closer_deadline_wins():
    prompts = npc.build_npc_prompts(
        summary(
            urgent_deadlines=[
                app_brief(application_id="far", company="먼곳", d_day=3),
                app_brief(application_id="near", company="가까운곳", d_day=0),
            ]
        )
    )
    # 에이전트당 하나라 탐색이 몫은 하나. 급한 쪽이 남아야 한다.
    assert len(prompts) == 1 and "가까운곳" in prompts[0]["text"]


def test_rejection_streak_brings_ha_eun_over():
    prompts = npc.build_npc_prompts(summary(rejection_streak_14d=3))
    [p] = [x for x in prompts if x["agent_id"] == "ha_eun"]

    assert p["kind"] == "rejection_streak"
    assert p["approach_player"] is True
    # 수치를 말하지 않는다. 탈락 3건이라고 세어 주는 건 위로가 아니다.
    assert "3" not in p["text"]


def test_streak_below_threshold_is_quiet():
    assert npc.build_npc_prompts(summary(rejection_streak_14d=2)) == []


def test_celebration_outranks_everything():
    prompts = npc.build_npc_prompts(
        summary(
            urgent_deadlines=[app_brief()],
            rejection_streak_14d=3,
            celebration={"application_id": "c1", "title": "카카오 - 백엔드"},
        )
    )
    assert prompts[0]["kind"] == "celebration" and prompts[0]["agent_id"] == "min_su"


def test_one_prompt_per_agent_and_max_three():
    prompts = npc.build_npc_prompts(
        summary(
            urgent_deadlines=[app_brief(application_id=f"a{i}", d_day=i) for i in range(3)],
            overdue=[app_brief(application_id="over", company="지난곳")],
            rejection_streak_14d=3,
            celebration={"application_id": "c1", "title": "축하"},
            next_event={**app_brief(), "next_event_at": datetime.utcnow().isoformat()},
        )
    )
    assert len(prompts) <= npc.MAX_PROMPTS
    assert len({p["agent_id"] for p in prompts}) == len(prompts)


def test_next_event_only_within_a_day():
    soon = datetime.utcnow() + timedelta(hours=5)
    later = datetime.utcnow() + timedelta(days=3)

    got = npc.build_npc_prompts(
        summary(next_event={**app_brief(), "next_event_at": soon.isoformat()})
    )
    assert [p["kind"] for p in got] == ["next_event"]

    quiet = npc.build_npc_prompts(
        summary(next_event={**app_brief(), "next_event_at": later.isoformat()})
    )
    assert quiet == []


def test_idle_checkin_only_when_nothing_active():
    [p] = npc.build_npc_prompts(summary(active_count=0, total=4))
    assert p["kind"] == "idle_checkin" and p["agent_id"] == "ha_eun"
    # 지원 기록 자체가 없는 새 사용자에게는 말을 걸지 않는다
    assert npc.build_npc_prompts(summary(active_count=0, total=0)) == []


def test_prompt_ids_are_stable():
    """같은 상황이면 같은 id. 닫아둔 말풍선이 새 id 로 되살아나면 안 된다."""
    s = summary(urgent_deadlines=[app_brief()])
    assert npc.build_npc_prompts(s)[0]["id"] == npc.build_npc_prompts(s)[0]["id"]


def test_desk_lights_up_on_urgent_deadline():
    buildings = {b["id"]: b for b in npc.build_buildings(summary(urgent_deadlines=[app_brief()]))}
    assert buildings["tracker"]["lit"] is True
    assert buildings["tracker"]["label"] == "D-1"
    assert buildings["tracker"]["badge"] == 1


def test_desk_says_dday_when_zero():
    b = npc.build_buildings(summary(urgent_deadlines=[app_brief(d_day=0)]))[0]
    assert b["label"] == "D-DAY"


def test_desk_dark_without_signal():
    assert npc.build_buildings(summary())[0]["lit"] is False


def test_moods_follow_prompts():
    prompts = npc.build_npc_prompts(summary(rejection_streak_14d=3))
    moods = {m["agent_id"]: m for m in npc.build_npc_moods(summary(), prompts)}

    assert moods["ha_eun"]["mood"] == "concerned"
    assert moods["ha_eun"]["wants_to_talk"] is True
    assert moods["ha_eun"]["approach_player"] is True
    assert moods["min_su"]["wants_to_talk"] is False
