import asyncio
import logging
import re
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import update as sa_update
from starlette.websockets import WebSocketState

from app.agents.graph import build_graph
from app.agents.profiles import AGENT_PROFILES
from app.api.middleware.auth import get_ws_user_id
from app.dependencies import async_session
from app.models.conversation import Conversation
from app.services.chat_service import (
    get_or_create_conversation,
    load_conversation_history,
    load_user_preferences,
    save_agent_message,
    save_user_message,
)
from app.services.emotion_service import get_emotion_summary, save_emotion_log

logger = logging.getLogger(__name__)
router = APIRouter()

GRAPH_TIMEOUT = 60  # seconds
MAX_MESSAGE_LENGTH = 2000

# 에이전트 이름 → ID 매핑
AGENT_NAME_TO_ID = {
    profile["name"]: agent_id
    for agent_id, profile in AGENT_PROFILES.items()
}
MENTION_PATTERN = re.compile(r"@(" + "|".join(AGENT_NAME_TO_ID.keys()) + r")")

# 에이전트 모듈 캐시 (매번 import 방지)
from app.agents.nodes import seo_yeon, jun_ho, ha_eun, min_su  # noqa: E402

_AGENT_MODULES = {
    "seo_yeon": seo_yeon, "jun_ho": jun_ho,
    "ha_eun": ha_eun, "min_su": min_su,
}

# 도구명 → 오피스 액션 매핑
TOOL_ACTION_MAP = {
    "search_jobs": "searching",
    "analyze_market": "analyzing",
    "resume_feedback": "reading",
    "mock_interview": "interview_prep",
    "breathing_exercise": "breathing",
    "get_motivation_content": "searching",
    "industry_insight": "analyzing",
    "schedule_routine": "typing",
    "save_job_preferences": "typing",
}


def parse_mentions(content: str) -> list[str]:
    mentioned = []
    for match in MENTION_PATTERN.finditer(content):
        agent_id = AGENT_NAME_TO_ID.get(match.group(1))
        if agent_id and agent_id not in mentioned:
            mentioned.append(agent_id)
    return mentioned


async def _safe_send(websocket: WebSocket, data: dict) -> bool:
    """WebSocket이 열려 있을 때만 전송. 실패 시 False."""
    try:
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json(data)
            return True
    except Exception:
        pass
    return False


def _get_office_action_for_response(resp: dict) -> str:
    """응답의 tool_calls를 분석하여 오피스 액션을 결정한다."""
    tool_calls = resp.get("tool_calls")
    if tool_calls and len(tool_calls) > 0:
        first_tool = tool_calls[0].get("name", "")
        return TOOL_ACTION_MAP.get(first_tool, "typing")
    return "typing"


@router.websocket("/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str) -> None:
    await websocket.accept()
    graph = build_graph()

    # 쿠키에서 user_id 추출 (없으면 게스트)
    ws_user_id = get_ws_user_id(websocket)
    user_id_str = str(ws_user_id) if ws_user_id else "anonymous"

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") != "user_message":
                continue

            user_message = data.get("content", "")
            if not user_message.strip():
                continue

            # 메시지 길이 제한
            if len(user_message) > MAX_MESSAGE_LENGTH:
                await _safe_send(websocket, {
                    "type": "error",
                    "message": f"메시지는 {MAX_MESSAGE_LENGTH}자 이내로 입력해주세요.",
                })
                continue

            try:
                chat_mode = data.get("mode", "group")
                target_agent = data.get("target_agent")
                mentioned_agents = parse_mentions(user_message)

                logger.info(f"Message: {user_message[:50]} | mode={chat_mode} | mentions={mentioned_agents}")

                # --- Phase 1: 유저 메시지 저장 + 컨텍스트 로드 (짧은 트랜잭션) ---
                async with async_session() as db:
                    conv = await get_or_create_conversation(
                        db, conversation_id, user_id=user_id_str
                    )
                    conv_id = conv.id
                    history = await load_conversation_history(db, conv_id)
                    preferences = await load_user_preferences(db, user_id_str)
                    emotion_summary = await get_emotion_summary(db, user_id_str)
                    await save_user_message(db, conv_id, user_message)
                    await db.commit()

                # --- Phase 2: LangGraph 실행 (트랜잭션 외부) ---
                try:
                    result = await asyncio.wait_for(
                        graph.ainvoke({
                            "messages": [],
                            "user_message": user_message,
                            "conversation_history": history,
                            "emotion": "",
                            "emotion_intensity": 0,
                            "intent": "",
                            "active_agents": [],
                            "agent_responses": [],
                            "conversation_id": conversation_id,
                            "user_id": user_id_str,
                            "user_preferences": preferences,
                            "emotion_history_summary": emotion_summary,
                            "task_plan": [],
                            "step_results": {},
                            "current_step": 0,
                        }),
                        timeout=GRAPH_TIMEOUT,
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Graph execution timed out ({GRAPH_TIMEOUT}s)")
                    await _safe_send(websocket, {
                        "type": "error",
                        "message": "응답 생성 시간이 초과되었습니다. 다시 시도해주세요.",
                    })
                    continue

                responses = result.get("agent_responses", [])
                emotion = result.get("emotion", "")
                emotion_intensity = result.get("emotion_intensity", 0)
                logger.info(f"Graph returned {len(responses)} responses: {[r['agent_id'] for r in responses]}")

                # DM 모드
                if chat_mode == "dm" and target_agent:
                    responses = [r for r in responses if r["agent_id"] == target_agent]
                    if not responses:
                        module = _AGENT_MODULES.get(target_agent)
                        if module:
                            resp = await module.run(result, is_primary=True)
                            responses = [resp]

                # @멘션 모드
                elif mentioned_agents:
                    filtered = [r for r in responses if r["agent_id"] in mentioned_agents]
                    responded_ids = {r["agent_id"] for r in filtered}
                    for agent_id in mentioned_agents:
                        if agent_id not in responded_ids:
                            module = _AGENT_MODULES.get(agent_id)
                            if module:
                                resp = await module.run(result, is_primary=len(filtered) == 0)
                                filtered.append(resp)
                    responses = filtered

                # --- Phase 3: 에이전트 응답 저장 + 감정 로그 (별도 트랜잭션) ---
                async with async_session() as db:
                    for resp in responses:
                        await save_agent_message(
                            db,
                            conv_id,
                            agent_id=resp["agent_id"],
                            content=resp["content"],
                            tool_calls=resp.get("tool_calls"),
                            emotion_tag=emotion or None,
                        )

                    # 감정 로그 저장
                    if emotion:
                        await save_emotion_log(
                            db, user_id_str, conversation_id,
                            emotion, emotion_intensity,
                            context=user_message[:100],
                        )

                    # 대화 제목 자동 생성 (첫 메시지 — atomic UPDATE로 경쟁 방지)
                    title_text = user_message[:50] + ("..." if len(user_message) > 50 else "")
                    await db.execute(
                        sa_update(Conversation)
                        .where(Conversation.id == conv_id, Conversation.title.is_(None))
                        .values(title=title_text)
                    )

                    await db.commit()

                logger.info(f"Sending {len(responses)} responses")

                # 응답 전송
                for resp in responses:
                    agent_id = resp["agent_id"]
                    content = resp["content"]
                    delay_ms = resp.get("delay_ms", 0)
                    tool_calls = resp.get("tool_calls")

                    if delay_ms > 0:
                        await asyncio.sleep(delay_ms / 1000)

                    # 실제 동작에 연동된 오피스 액션 전송
                    office_action = _get_office_action_for_response(resp)
                    await _safe_send(websocket, {
                        "type": "agent_typing",
                        "agent_id": agent_id,
                        "office_action": office_action,
                    })

                    await asyncio.sleep(0.5)

                    # tool_result 이벤트 전송 (도구 결과가 있을 때)
                    if tool_calls:
                        for tc in tool_calls:
                            await _safe_send(websocket, {
                                "type": "tool_result",
                                "agent_id": agent_id,
                                "tool_name": tc["name"],
                                "data": tc.get("result", {}),
                            })

                    await _safe_send(websocket, {
                        "type": "agent_message_chunk",
                        "agent_id": agent_id,
                        "chunk": content,
                        "is_final": True,
                    })

                # idle 복귀 + 감정 상태 전송
                await _safe_send(websocket, {
                    "type": "office_state",
                    "agents": {
                        aid: {
                            "action": "idle",
                            "position": AGENT_PROFILES[aid]["office_position"],
                        }
                        for aid in AGENT_PROFILES
                    },
                    "emotion": emotion,
                })

            except Exception as e:
                logger.error(f"Error processing message: {e}\n{traceback.format_exc()}")
                await _safe_send(websocket, {
                    "type": "error",
                    "message": "메시지 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conversation_id}")
