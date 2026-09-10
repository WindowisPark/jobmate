"""방(월드) 상태 — 지원 데이터를 방이 반응할 신호로 바꿔 내려준다.

프런트의 `MallangRoom` 은 이 응답만 보고 책상을 켜고 말풍선을 띄운다.
계산은 전부 `build_application_summary` 하나에서 나온다(chat 컨텍스트와 같은 진실).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.auth import get_current_user_id
from app.dependencies import get_db, get_redis
from app.services import npc_prompt_service as npc
from app.services.application_service import build_application_summary
from app.services.chat_service import get_or_create_conversation, save_agent_message

router = APIRouter()

DISMISS_TTL = 60 * 60 * 24  # 하루 지나면 다시 말을 건다
ACK_TTL = 60 * 60 * 24 * 7  # 축하는 일주일에 한 번이면 충분하다


def _dismiss_key(user_id: uuid.UUID, prompt_id: str) -> str:
    return f"npc_prompt:dismissed:{user_id}:{prompt_id}"


def _ack_key(user_id: uuid.UUID, app_id: str) -> str:
    return f"celebration:acked:{user_id}:{app_id}"


@router.get("/state")
async def world_state(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    summary = await build_application_summary(db, user_id)

    celebration = summary.get("celebration")
    if celebration and await redis.get(_ack_key(user_id, celebration["application_id"])):
        summary = {**summary, "celebration": None}

    prompts = npc.build_npc_prompts(summary)
    # 닫은 말풍선은 하루 동안 다시 띄우지 않는다
    keys = [_dismiss_key(user_id, p["id"]) for p in prompts]
    if keys:
        dismissed = await redis.mget(keys)
        prompts = [p for p, hit in zip(prompts, dismissed, strict=True) if not hit]

    return {
        "today": summary["today"],
        "signals": summary,
        "buildings": npc.build_buildings(summary),
        "npcs": npc.build_npc_moods(summary, prompts),
        "npc_prompts": prompts,
    }


@router.post("/prompts/{prompt_id}/accept")
async def accept_prompt(
    prompt_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict:
    """말풍선을 눌렀다. 그 대사를 DM 에 에이전트 메시지로 남긴다.

    여기서 LLM 은 부르지 않는다. 사용자가 답장을 보낼 때 비로소 모델이 돈다.
    이렇게 저장해 두면 그 답장의 history 에 이 대사가 들어가 맥락이 이어진다.
    """
    summary = await build_application_summary(db, user_id)
    prompt = next((p for p in npc.build_npc_prompts(summary) if p["id"] == prompt_id), None)
    if prompt is None:
        raise HTTPException(status_code=404, detail="이미 지난 이야기예요")

    room_id = f"dm-{prompt['agent_id']}"
    conv = await get_or_create_conversation(db, room_id, user_id)
    await save_agent_message(db, conv.id, prompt["agent_id"], prompt["text"])
    await db.commit()

    await redis.setex(_dismiss_key(user_id, prompt_id), DISMISS_TTL, "1")
    return {
        "room_id": room_id,
        "agent_id": prompt["agent_id"],
        "text": prompt["text"],
        "suggested_reply": prompt.get("suggested_reply", ""),
    }


@router.post("/prompts/{prompt_id}/dismiss", status_code=204)
async def dismiss_prompt(
    prompt_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    redis: Redis = Depends(get_redis),
) -> None:
    await redis.setex(_dismiss_key(user_id, prompt_id), DISMISS_TTL, "1")


@router.post("/celebrations/{app_id}/ack", status_code=204)
async def ack_celebration(
    app_id: str,
    user_id: uuid.UUID = Depends(get_current_user_id),
    redis: Redis = Depends(get_redis),
) -> None:
    await redis.setex(_ack_key(user_id, app_id), ACK_TTL, "1")
