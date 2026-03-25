import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.services.chat_service import ensure_anonymous_user

router = APIRouter()


@router.get("")
async def list_conversations(db: AsyncSession = Depends(get_db)) -> list[dict]:
    """대화 목록을 최신순으로 반환한다."""
    # 각 대화의 마지막 메시지 시각과 메시지 수를 함께 조회
    result = await db.execute(
        select(
            Conversation,
            func.count(Message.id).label("message_count"),
            func.max(Message.created_at).label("last_message_at"),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .group_by(Conversation.id)
        .order_by(Conversation.updated_at.desc())
    )

    conversations = []
    for row in result.all():
        conv = row[0]
        conversations.append({
            "id": str(conv.id),
            "title": conv.title,
            "message_count": row[1],
            "last_message_at": row[2].isoformat() if row[2] else None,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat(),
        })

    return conversations


@router.post("")
async def create_conversation(db: AsyncSession = Depends(get_db)) -> dict:
    """새 대화를 생성한다."""
    # TODO: JWT 인증 후 실제 user_id 사용
    anonymous_user_id = await ensure_anonymous_user(db)

    conv = Conversation(
        id=uuid.uuid4(),
        user_id=anonymous_user_id,
        title=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(conv)
    await db.commit()

    return {
        "id": str(conv.id),
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
    }


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """대화 상세 정보와 메시지 목록을 반환한다."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .options(selectinload(Conversation.messages))
    )
    conv = result.scalar_one_or_none()

    if conv is None:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")

    messages = sorted(conv.messages, key=lambda m: m.created_at)

    return {
        "id": str(conv.id),
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "updated_at": conv.updated_at.isoformat(),
        "messages": [
            {
                "id": str(msg.id),
                "sender_type": msg.sender_type,
                "agent_id": msg.agent_id,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "tool_results": msg.tool_results,
                "emotion_tag": msg.emotion_tag,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ],
    }


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """대화와 관련 메시지를 삭제한다."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()

    if conv is None:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")

    # 메시지 먼저 삭제
    msg_result = await db.execute(
        select(Message).where(Message.conversation_id == conversation_id)
    )
    for msg in msg_result.scalars().all():
        await db.delete(msg)

    await db.delete(conv)
    await db.commit()

    return {"detail": "대화가 삭제되었습니다"}
