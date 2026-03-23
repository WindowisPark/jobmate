from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/chat/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str) -> None:
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            # TODO: authenticate via token query param
            # TODO: pass message to LangGraph agent pipeline
            # TODO: stream agent responses back via WebSocket

            await websocket.send_json({
                "type": "agent_message_chunk",
                "agent_id": "ha_eun",
                "chunk": "연결 성공! 아직 에이전트가 구현되지 않았어요.",
                "is_final": True,
            })
    except WebSocketDisconnect:
        pass
