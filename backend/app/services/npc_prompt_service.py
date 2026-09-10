"""NPC 선제 대사 — 방이 데이터를 알고 먼저 말을 걸게 만든다.

**LLM 을 부르지 않는다.** 전부 템플릿이다. 이유가 셋이다.
- 방에 들어올 때마다 모델을 부르면 비용이 사용자 수에 비례해 늘어난다.
- 같은 상황에서 같은 말이 나와야 테스트할 수 있다.
- 말풍선은 대화의 시작점일 뿐이다. 진짜 대화는 사용자가 답장할 때 시작된다.

말풍선을 누르면 그 대사가 DM 에 에이전트 메시지로 저장된다(routes/world.py).
그때부터는 history 에 들어가 LLM 이 맥락으로 읽는다.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.services.application_service import REJECTION_STREAK_MIN

# 한 번에 이만큼만 띄운다. 셋 넘게 뜨면 방이 시끄럽다.
MAX_PROMPTS = 3

# 우선순위가 높은 순으로 고른다. 에이전트당 하나만.
PRIORITY = {
    "celebration": 99,
    "rejection_streak": 95,
    "next_event": 60,
    "idle_checkin": 10,
}

IDLE_DAYS = 7  # 이만큼 아무 활동이 없으면 안부를 묻는다


def _deadline_prompt(app: dict) -> dict:
    """마감 임박 — 탐색이. D-day 가 가까울수록 위로 온다."""
    d = app.get("d_day")
    doc = app.get("resume_document")
    when = "오늘" if d == 0 else "내일" if d == 1 else f"{d}일 뒤"
    if doc:
        text = f"{app['company']} {when} 마감이야. {doc}로 낼 거지?"
        reply = f"응, {doc}로 낼게. 체크리스트 좀 봐줘"
    else:
        text = f"{app['company']} {when} 마감인데 이력서 아직 안 골랐어."
        reply = "어떤 이력서로 낼지 같이 정하자"
    return {
        "id": f"deadline:{app['application_id']}:{app.get('deadline_at')}",
        "agent_id": "jun_ho",
        "kind": "deadline",
        "priority": 100 - (d or 0) * 10,
        "text": text,
        "suggested_reply": reply,
        "application_id": app["application_id"],
    }


def build_npc_prompts(summary: dict, *, now: datetime | None = None) -> list[dict]:
    """지원 현황 요약에서 말풍선을 만든다. 순수 함수 — DB 도 LLM 도 안 탄다."""
    now = now or datetime.utcnow()
    candidates: list[dict] = []

    for app in summary.get("urgent_deadlines", [])[:3]:
        candidates.append(_deadline_prompt(app))

    overdue = summary.get("overdue", [])
    if overdue:
        first = overdue[0]
        candidates.append(
            {
                "id": f"overdue:{first['application_id']}",
                "agent_id": "jun_ho",
                "kind": "overdue",
                "priority": 70,
                "text": f"{first['company']} 마감 지났어. 아직 진행 중으로 두고 있네?",
                "suggested_reply": "상태 정리 좀 도와줘",
                "application_id": first["application_id"],
            }
        )

    streak = summary.get("rejection_streak_14d", 0)
    if streak >= REJECTION_STREAK_MIN:
        candidates.append(
            {
                "id": f"streak:{summary.get('today')}:{streak}",
                "agent_id": "ha_eun",
                "kind": "rejection_streak",
                "priority": PRIORITY["rejection_streak"],
                "text": "요즘 결과가 계속 아쉬웠지. 잠깐 앉았다 갈래?",
                "suggested_reply": "응, 좀 지치네",
                "approach_player": True,
            }
        )

    celebration = summary.get("celebration")
    if celebration:
        candidates.append(
            {
                "id": f"celebration:{celebration['application_id']}",
                "agent_id": "min_su",
                "kind": "celebration",
                "priority": PRIORITY["celebration"],
                "text": f"{celebration['title']} 붙었다며! 야 이거 진짜 축하해 ㅋㅋ",
                "suggested_reply": "고마워 ㅎㅎ 다음은 뭘 준비할까?",
                "application_id": celebration["application_id"],
            }
        )

    nxt = summary.get("next_event")
    if nxt and nxt.get("next_event_at"):
        try:
            when = datetime.fromisoformat(nxt["next_event_at"])
            soon = when - now <= timedelta(hours=24)
        except (TypeError, ValueError):
            soon = False
        if soon:
            candidates.append(
                {
                    "id": f"event:{nxt['application_id']}:{nxt['next_event_at'][:10]}",
                    "agent_id": "seo_yeon",
                    "kind": "next_event",
                    "priority": PRIORITY["next_event"],
                    "text": f"곧 {nxt['company']} {nxt['status_label']}이네. 한 번 돌려볼까?",
                    "suggested_reply": "응, 모의로 한 번 해보자",
                    "application_id": nxt["application_id"],
                }
            )

    # 진행 중이 없어도 방금 붙었거나 최근에 결과가 난 사람에게 "쉬고 있구나" 는 어긋난다
    quiet = not celebration and not summary.get("recent_outcomes")
    if quiet and summary.get("active_count", 0) == 0 and summary.get("total", 0) > 0:
        candidates.append(
            {
                "id": f"idle:{summary.get('today')}",
                "agent_id": "ha_eun",
                "kind": "idle_checkin",
                "priority": PRIORITY["idle_checkin"],
                "text": "요즘 좀 쉬고 있구나. 그것도 필요한 시간이야.",
                "suggested_reply": "슬슬 다시 시작해볼까 해",
            }
        )

    return _pick(candidates)


def _pick(candidates: list[dict]) -> list[dict]:
    """우선순위 순으로, 에이전트당 하나씩, 최대 MAX_PROMPTS 개."""
    seen: set[str] = set()
    picked: list[dict] = []
    for c in sorted(candidates, key=lambda x: -x["priority"]):
        if c["agent_id"] in seen:
            continue
        seen.add(c["agent_id"])
        picked.append(c)
        if len(picked) >= MAX_PROMPTS:
            break
    return picked


def build_buildings(summary: dict) -> list[dict]:
    """가구가 데이터에 반응한다. 마감이 임박하면 책상에 불이 켜진다."""
    urgent = summary.get("urgent_deadlines", [])
    overdue = summary.get("overdue", [])
    return [
        {
            "id": "tracker",
            "lit": bool(urgent or overdue),
            "badge": len(urgent) + len(overdue),
            "label": _lit_label(urgent, overdue),
            "celebrating": bool(summary.get("celebration")),
        },
        {"id": "documents", "lit": False, "badge": 0, "label": None, "celebrating": False},
    ]


def _lit_label(urgent: list[dict], overdue: list[dict]) -> str | None:
    if urgent:
        d = urgent[0].get("d_day")
        return "D-DAY" if d == 0 else f"D-{d}"
    if overdue:
        return "마감 지남"
    return None


def build_npc_moods(summary: dict, prompts: list[dict]) -> list[dict]:
    """NPC 표정. 말풍선이 있으면 말 걸고 싶은 상태."""
    by_agent = {p["agent_id"]: p for p in prompts}
    moods = []
    for agent_id in ("seo_yeon", "jun_ho", "ha_eun", "min_su"):
        p = by_agent.get(agent_id)
        mood = "normal"
        if p:
            mood = {"celebration": "excited", "rejection_streak": "concerned"}.get(
                p["kind"], "normal"
            )
        moods.append(
            {
                "agent_id": agent_id,
                "mood": mood,
                "wants_to_talk": p is not None,
                "approach_player": bool(p and p.get("approach_player")),
            }
        )
    return moods
