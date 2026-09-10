"""플래너 오버라이드 — 지원 현황이 담당자를 앞으로 당긴다."""

import importlib

planner = importlib.import_module("app.agents.planner")


def steps(*agents) -> list[dict]:
    return [
        {
            "step_id": i,
            "agent_id": a,
            "role": "primary" if i == 0 else "assist",
            "action_hint": "x",
            "depends_on": [],
            "tool_hint": None,
        }
        for i, a in enumerate(agents)
    ]


def urgent(**over) -> dict:
    base = {"rejection_streak_14d": 0, "urgent_deadlines": [], "celebration": None}
    base.update(over)
    return base


def test_no_summary_changes_nothing():
    s = steps("ha_eun")
    assert planner._apply_tracker_override(s, None, "general") == s


def test_urgent_deadline_brings_jun_ho_to_the_front():
    got = planner._apply_tracker_override(
        steps("ha_eun"), urgent(urgent_deadlines=[{"d_day": 1}]), "general"
    )
    assert [s["agent_id"] for s in got] == ["jun_ho", "ha_eun"]
    assert got[0]["tool_hint"] == "get_my_applications"
    # step_id 는 다시 매겨진다
    assert [s["step_id"] for s in got] == [0, 1]


def test_deadline_override_skips_unrelated_intent():
    got = planner._apply_tracker_override(
        steps("ha_eun"), urgent(urgent_deadlines=[{"d_day": 1}]), "mental_care"
    )
    assert [s["agent_id"] for s in got] == ["ha_eun"]


def test_existing_agent_is_not_duplicated():
    got = planner._apply_tracker_override(
        steps("jun_ho", "seo_yeon"), urgent(urgent_deadlines=[{"d_day": 0}]), "job_search"
    )
    assert [s["agent_id"] for s in got] == ["jun_ho", "seo_yeon"]


def test_rejection_streak_brings_ha_eun_over():
    got = planner._apply_tracker_override(steps("min_su"), urgent(rejection_streak_14d=3), "general")
    assert got[0]["agent_id"] == "ha_eun"


def test_streak_and_deadline_both_fire_without_clobbering():
    got = planner._apply_tracker_override(
        steps("min_su"),
        urgent(rejection_streak_14d=3, urgent_deadlines=[{"d_day": 1}]),
        "general",
    )
    ids = [s["agent_id"] for s in got]
    assert set(ids) == {"jun_ho", "ha_eun", "min_su"}
    assert [s["step_id"] for s in got] == list(range(len(got)))


def test_celebration_appends_min_su_as_assist():
    got = planner._apply_tracker_override(
        steps("seo_yeon"), urgent(celebration={"title": "카카오"}), "general"
    )
    assert got[-1]["agent_id"] == "min_su" and got[-1]["role"] == "assist"


def test_emotion_override_still_works_through_shared_helper():
    got = planner._apply_emotion_override(steps("jun_ho"), "anxious", 5)
    assert [s["agent_id"] for s in got] == ["ha_eun", "jun_ho"]


def test_depends_on_shifts_when_a_step_is_prepended():
    base = steps("seo_yeon", "min_su")
    base[1]["depends_on"] = [0]
    got = planner._prepend_step(base, "ha_eun", "emotional_support")
    assert [s["agent_id"] for s in got] == ["ha_eun", "seo_yeon", "min_su"]
    # 원래 0번을 기다리던 단계는 이제 1번을 기다려야 한다
    assert got[2]["depends_on"] == [1]
