"""LLM 기반 태스크 플래너 — 사용자 의도를 분석하여 에이전트 실행 계획을 생성한다."""

import json
import logging
from typing import Literal, TypedDict

from app.agents.state import JobMateState
from app.services.application_service import REJECTION_STREAK_MIN
from app.services.llm_service import generate_response

logger = logging.getLogger(__name__)


class TaskStep(TypedDict):
    step_id: int
    agent_id: str
    role: Literal["primary", "assist"]
    action_hint: str
    depends_on: list[int]
    tool_hint: str | None


# 단순 의도에 대한 Fast-path (LLM 호출 없이 바로 계획 생성)
FAST_PATH_ROUTING: dict[str, list[TaskStep]] = {
    "resume_interview": [
        {
            "step_id": 0,
            "agent_id": "seo_yeon",
            "role": "primary",
            "action_hint": "resume_or_interview",
            "depends_on": [],
            "tool_hint": None,
        },
        {
            "step_id": 1,
            "agent_id": "min_su",
            "role": "assist",
            "action_hint": "encouragement",
            "depends_on": [],
            "tool_hint": None,
        },
    ],
    "job_search": [
        {
            "step_id": 0,
            "agent_id": "jun_ho",
            "role": "primary",
            "action_hint": "search_jobs",
            "depends_on": [],
            "tool_hint": "search_jobs",
        },
        {
            "step_id": 1,
            "agent_id": "seo_yeon",
            "role": "assist",
            "action_hint": "career_tip",
            "depends_on": [],
            "tool_hint": None,
        },
    ],
    "mental_care": [
        {
            "step_id": 0,
            "agent_id": "ha_eun",
            "role": "primary",
            "action_hint": "emotional_support",
            "depends_on": [],
            "tool_hint": None,
        },
        {
            "step_id": 1,
            "agent_id": "min_su",
            "role": "assist",
            "action_hint": "encouragement",
            "depends_on": [],
            "tool_hint": None,
        },
    ],
    "career_advice": [
        {
            "step_id": 0,
            "agent_id": "min_su",
            "role": "primary",
            "action_hint": "career_advice",
            "depends_on": [],
            "tool_hint": None,
        },
        {
            "step_id": 1,
            "agent_id": "seo_yeon",
            "role": "assist",
            "action_hint": "practical_tip",
            "depends_on": [],
            "tool_hint": None,
        },
    ],
    "general": [
        {
            "step_id": 0,
            "agent_id": "ha_eun",
            "role": "primary",
            "action_hint": "general_chat",
            "depends_on": [],
            "tool_hint": None,
        },
    ],
}

PLANNER_PROMPT = """\
너는 멀티 에이전트 시스템의 태스크 플래너야. 사용자의 메시지를 분석하여 실행 계획을 JSON으로 반환해.

사용 가능한 에이전트:
- seo_yeon: 커리어 코치 (이력서 피드백, 면접 준비). 도구: resume_feedback, mock_interview, get_my_applications
- jun_ho: 취업 리서처 (채용공고 검색, 시장 분석, 내 지원 현황 조회·상태 변경).
  도구: search_jobs, analyze_market, save_job_preferences, get_my_applications, update_application_status
- ha_eun: 멘탈 케어 (감정 케어, 호흡 운동, 루틴 관리). 도구: breathing_exercise, schedule_routine, get_my_applications
- min_su: 현직 멘토 (동기부여, 업계 인사이트). 도구: get_motivation_content, industry_insight, get_my_applications

규칙:
1. 단순 질문은 1~2 step으로 충분해
2. 복합 요청("공고 찾고 면접 준비해줘")은 depends_on으로 체이닝해
3. 사용자가 매우 힘든 상태(감정 강도 4 이상)면 ha_eun을 첫 step에 넣어
4. step_id는 0부터 시작
5. depends_on은 해당 step이 완료된 후에 실행해야 할 때 사용

사용자 감정: {emotion} (강도: {intensity})
분류된 의도: {intent}

JSON 형식으로만 반환해:
{{
  "steps": [
    {{
      "step_id": 0,
      "agent_id": "에이전트_id",
      "role": "primary" | "assist",
      "action_hint": "수행할 작업 설명",
      "depends_on": [],
      "tool_hint": "도구명_또는_null"
    }}
  ]
}}

JSON만 반환해. 다른 텍스트 없이."""


def _is_simple_intent(intent: str, emotion: str, intensity: int) -> bool:
    """Fast-path 사용 가능 여부를 판단한다."""
    # 높은 감정 강도 + 부정적 감정이면 플래너 사용
    if intensity >= 4 and emotion in ("anxious", "depressed", "angry", "frustrated"):
        return False
    return intent in FAST_PATH_ROUTING


def _prepend_step(
    steps: list[TaskStep],
    agent_id: str,
    action_hint: str,
    tool_hint: str | None = None,
) -> list[TaskStep]:
    """이미 있는 에이전트면 그대로 두고, 없으면 맨 앞에 끼운다.

    step_id 와 depends_on 재정렬은 여기 한 곳에서만 한다.
    감정 오버라이드와 트래커 오버라이드가 같은 로직을 복사하면 어긋난다.
    """
    if any(s["agent_id"] == agent_id for s in steps):
        return steps
    head: TaskStep = {
        "step_id": -1,
        "agent_id": agent_id,
        "role": "primary",
        "action_hint": action_hint,
        "depends_on": [],
        "tool_hint": tool_hint,
    }
    steps = [head] + steps
    for i, step in enumerate(steps):
        step["step_id"] = i
        step["depends_on"] = [d + 1 for d in step["depends_on"] if d >= 0]
    return steps


def _apply_emotion_override(steps: list[TaskStep], emotion: str, intensity: int) -> list[TaskStep]:
    """감정 강도가 높으면 ha_eun 을 첫 번째로 삽입한다."""
    if intensity >= 4 and emotion in ("anxious", "depressed", "angry", "frustrated"):
        steps = _prepend_step(steps, "ha_eun", "emotional_support")
    return steps


def _apply_tracker_override(
    steps: list[TaskStep], summary: dict | None, intent: str
) -> list[TaskStep]:
    """지원 현황이 먼저 말해야 할 때 담당자를 앞으로 당긴다.

    감정 오버라이드 다음에 부른다. 이미 ha_eun 이 앞에 있으면 _prepend_step 이 건너뛴다.
    """
    if not summary:
        return steps

    if summary.get("rejection_streak_14d", 0) >= REJECTION_STREAK_MIN:
        steps = _prepend_step(steps, "ha_eun", "emotional_support")

    if summary.get("urgent_deadlines") and intent in (
        "general",
        "job_search",
        "resume_interview",
    ):
        steps = _prepend_step(steps, "jun_ho", "deadline_reminder", "get_my_applications")

    if summary.get("celebration") and not any(s["agent_id"] == "min_su" for s in steps):
        steps = steps + [
            {
                "step_id": len(steps),
                "agent_id": "min_su",
                "role": "assist",
                "action_hint": "celebration",
                "depends_on": [],
                "tool_hint": None,
            }
        ]
    return steps


async def plan_tasks(state: JobMateState) -> dict:
    """사용자 메시지를 분석하여 에이전트 실행 계획을 생성한다."""
    intent = state.get("intent", "general")
    emotion = state.get("emotion", "neutral")
    intensity = state.get("emotion_intensity", 2)
    user_message = state.get("user_message", "")

    # Fast-path: 단순 의도는 LLM 호출 없이 처리
    if _is_simple_intent(intent, emotion, intensity):
        steps = [dict(s) for s in FAST_PATH_ROUTING.get(intent, FAST_PATH_ROUTING["general"])]
        steps = _apply_emotion_override(steps, emotion, intensity)
        steps = _apply_tracker_override(steps, state.get("application_summary"), intent)
        return {
            "task_plan": steps,
            "step_results": {},
            "current_step": 0,
        }

    # LLM 기반 계획 생성
    prompt = PLANNER_PROMPT.format(
        emotion=emotion,
        intensity=intensity,
        intent=intent,
    )

    try:
        raw = await generate_response(prompt, user_message)
        cleaned = (
            raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        )
        result = json.loads(cleaned)
        steps = result.get("steps", [])

        # 검증: 유효한 agent_id만 허용
        valid_agents = {"seo_yeon", "jun_ho", "ha_eun", "min_su"}
        steps = [s for s in steps if s.get("agent_id") in valid_agents]

        if not steps:
            raise ValueError("Empty plan")

        steps = _apply_emotion_override(steps, emotion, intensity)
        steps = _apply_tracker_override(steps, state.get("application_summary"), intent)

        return {
            "task_plan": steps,
            "step_results": {},
            "current_step": 0,
        }

    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Planner LLM failed, falling back to fast-path: {e}")
        steps = [dict(s) for s in FAST_PATH_ROUTING.get(intent, FAST_PATH_ROUTING["general"])]
        steps = _apply_emotion_override(steps, emotion, intensity)
        steps = _apply_tracker_override(steps, state.get("application_summary"), intent)
        return {
            "task_plan": steps,
            "step_results": {},
            "current_step": 0,
        }
