import asyncio
import logging
import re
import traceback

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.graph import build_graph
from app.agents.profiles import AGENT_PROFILES

logger = logging.getLogger(__name__)
router = APIRouter()

# 에이전트 이름 → ID 매핑
AGENT_NAME_TO_ID = {
    profile["name"]: agent_id
    for agent_id, profile in AGENT_PROFILES.items()
}
MENTION_PATTERN = re.compile(r"@(" + "|".join(AGENT_NAME_TO_ID.keys()) + r")")


def parse_mentions(content: str) -> list[str]:
    mentioned = []
    for match in MENTION_PATTERN.finditer(content):
        agent_id = AGENT_NAME_TO_ID.get(match.group(1))
        if agent_id and agent_id not in mentioned:
            mentioned.append(agent_id)
    return mentioned


@router.websocket("/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str) -> None:
    await websocket.accept()
    graph = build_graph()

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") != "user_message":
                continue

            user_message = data.get("content", "")
            if not user_message.strip():
                continue

            try:
                chat_mode = data.get("mode", "group")
                target_agent = data.get("target_agent")
                mentioned_agents = parse_mentions(user_message)

                logger.info(f"Message: {user_message[:50]} | mode={chat_mode} | mentions={mentioned_agents}")

                # LangGraph 실행
                result = await graph.ainvoke({
                    "messages": [],
                    "user_message": user_message,
                    "emotion": "",
                    "emotion_intensity": 0,
                    "intent": "",
                    "active_agents": [],
                    "agent_responses": [],
                    "conversation_id": conversation_id,
                    "user_id": "anonymous",
                })

                responses = result.get("agent_responses", [])
                logger.info(f"Graph returned {len(responses)} responses: {[r['agent_id'] for r in responses]}")

                # DM 모드
                if chat_mode == "dm" and target_agent:
                    responses = [r for r in responses if r["agent_id"] == target_agent]
                    if not responses:
                        from app.agents.nodes import seo_yeon, jun_ho, ha_eun, min_su
                        modules = {
                            "seo_yeon": seo_yeon, "jun_ho": jun_ho,
                            "ha_eun": ha_eun, "min_su": min_su,
                        }
                        module = modules.get(target_agent)
                        if module:
                            resp = await module.run(result, is_primary=True)
                            responses = [resp]

                # @멘션 모드
                elif mentioned_agents:
                    filtered = [r for r in responses if r["agent_id"] in mentioned_agents]
                    responded_ids = {r["agent_id"] for r in filtered}
                    for agent_id in mentioned_agents:
                        if agent_id not in responded_ids:
                            from app.agents.nodes import seo_yeon, jun_ho, ha_eun, min_su
                            modules = {
                                "seo_yeon": seo_yeon, "jun_ho": jun_ho,
                                "ha_eun": ha_eun, "min_su": min_su,
                            }
                            module = modules.get(agent_id)
                            if module:
                                resp = await module.run(result, is_primary=len(filtered) == 0)
                                filtered.append(resp)
                    responses = filtered

                logger.info(f"Sending {len(responses)} responses")

                # 응답 전송
                for resp in responses:
                    agent_id = resp["agent_id"]
                    content = resp["content"]
                    delay_ms = resp.get("delay_ms", 0)

                    if delay_ms > 0:
                        await asyncio.sleep(delay_ms / 1000)

                    await websocket.send_json({
                        "type": "agent_typing",
                        "agent_id": agent_id,
                        "office_action": "thinking",
                    })

                    await asyncio.sleep(0.5)

                    await websocket.send_json({
                        "type": "agent_message_chunk",
                        "agent_id": agent_id,
                        "chunk": content,
                        "is_final": True,
                    })

                # idle 복귀
                await websocket.send_json({
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
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })

    except WebSocketDisconnect:
        pass
