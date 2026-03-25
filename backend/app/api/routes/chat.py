import asyncio
import logging
import re
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.agents.graph import build_graph
from app.agents.profiles import AGENT_PROFILES
from app.api.middleware.auth import get_ws_user_id
from app.dependencies import async_session
from app.services.chat_service import (
    get_or_create_conversation,
    load_conversation_history,
    save_agent_message,
    save_user_message,
)

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

                # --- DB 영속화 ---
                async with async_session() as db:
                    try:
                        conv = await get_or_create_conversation(
                            db, conversation_id, user_id=user_id_str
                        )
                        history = await load_conversation_history(db, conv.id)
                        await save_user_message(db, conv.id, user_message)

                        # LangGraph 실행 (타임아웃 적용)
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
                            }),
                            timeout=GRAPH_TIMEOUT,
                        )

                        responses = result.get("agent_responses", [])
                        emotion = result.get("emotion", "")
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

                        # 에이전트 응답 DB 저장
                        for resp in responses:
                            await save_agent_message(
                                db,
                                conv.id,
                                agent_id=resp["agent_id"],
                                content=resp["content"],
                                tool_calls=resp.get("tool_calls"),
                                emotion_tag=emotion or None,
                            )

                        if conv.title is None:
                            conv.title = user_message[:50] + ("..." if len(user_message) > 50 else "")

                        await db.commit()

                    except asyncio.TimeoutError:
                        await db.rollback()
                        logger.error(f"Graph execution timed out ({GRAPH_TIMEOUT}s)")
                        await _safe_send(websocket, {
                            "type": "error",
                            "message": "응답 생성 시간이 초과되었습니다. 다시 시도해주세요.",
                        })
                        continue

                    except Exception:
                        await db.rollback()
                        raise

                logger.info(f"Sending {len(responses)} responses")

                # 응답 전송
                for resp in responses:
                    agent_id = resp["agent_id"]
                    content = resp["content"]
                    delay_ms = resp.get("delay_ms", 0)

                    if delay_ms > 0:
                        await asyncio.sleep(delay_ms / 1000)

                    await _safe_send(websocket, {
                        "type": "agent_typing",
                        "agent_id": agent_id,
                        "office_action": "thinking",
                    })

                    await asyncio.sleep(0.5)

                    await _safe_send(websocket, {
                        "type": "agent_message_chunk",
                        "agent_id": agent_id,
                        "chunk": content,
                        "is_final": True,
                    })

                # idle 복귀
                await _safe_send(websocket, {
                    "type": "office_state",
                    "agents": {
                        aid: {
                            "action": "idle",
                            "position": AGENT_PROFILES[aid]["office_position"],
                        }
                        for aid in AGENT_PROFILES
                    },
                })

            except Exception as e:
                logger.error(f"Error processing message: {e}\n{traceback.format_exc()}")
                await _safe_send(websocket, {
                    "type": "error",
                    "message": "메시지 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {conversation_id}")
