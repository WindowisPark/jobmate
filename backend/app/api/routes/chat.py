import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.graph import build_graph
from app.agents.profiles import AGENT_PROFILES

router = APIRouter()

# Tool → 오피스 행동 매핑
TOOL_OFFICE_ACTIONS = {
    "search_jobs": "searching",
    "resume_feedback": "reading",
    "mock_interview": "talking",
    "breathing_exercise": "meditating",
    "schedule_routine": "typing",
    "get_motivation_content": "searching",
    "analyze_market": "reading",
    "industry_insight": "thinking",
}


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

            # 에이전트 응답을 순차적으로 WebSocket 전송
            for resp in result.get("agent_responses", []):
                agent_id = resp["agent_id"]
                content = resp["content"]
                delay_ms = resp.get("delay_ms", 0)

                # 딜레이 적용 (자연스러운 타이밍)
                if delay_ms > 0:
                    await asyncio.sleep(delay_ms / 1000)

                # 타이핑 시작 알림
                await websocket.send_json({
                    "type": "agent_typing",
                    "agent_id": agent_id,
                    "office_action": "thinking",
                })

                # 타이핑 효과 대기
                await asyncio.sleep(0.5)

                # 오피스 행동 업데이트
                await websocket.send_json({
                    "type": "office_state",
                    "agents": {
                        aid: {
                            "action": "talking" if aid == agent_id else "idle",
                            "position": AGENT_PROFILES[aid]["office_position"],
                        }
                        for aid in AGENT_PROFILES
                    },
                })

                # 메시지 청크 전송 (현재는 한번에, 추후 스트리밍 분할 가능)
                await websocket.send_json({
                    "type": "agent_message_chunk",
                    "agent_id": agent_id,
                    "chunk": content,
                    "is_final": True,
                })

            # 모든 에이전트 idle로 복귀
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

    except WebSocketDisconnect:
        pass
