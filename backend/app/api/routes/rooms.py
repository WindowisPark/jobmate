import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_db
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.middleware.auth import get_optional_user_id
from app.services.chat_service import ANONYMOUS_USER_ID, ensure_anonymous_user

router = APIRouter()


async def _resolve_user_id(request: Request, db: AsyncSession) -> uuid.UUID:
    """인증된 유저면 user_id, 게스트면 anonymous user_id 반환."""
    user_id = await get_optional_user_id(request)
    if user_id:
        return user_id
    return await ensure_anonymous_user(db)


@router.get("")
async def list_conversations(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """현재 유저의 대화 목록을 최신순으로 반환한다."""
    user_id = await _resolve_user_id(request, db)

    result = await db.execute(
        select(
            Conversation,
            func.count(Message.id).label("message_count"),
            func.max(Message.created_at).label("last_message_at"),
        )
        .outerjoin(Message, Message.conversation_id == Conversation.id)
        .where(Conversation.user_id == user_id)
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
async def create_conversation(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """새 대화를 생성한다."""
    user_id = await _resolve_user_id(request, db)

    conv = Conversation(
        id=uuid.uuid4(),
        user_id=user_id,
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
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """대화 상세 정보와 메시지 목록을 반환한다."""
    user_id = await _resolve_user_id(request, db)

    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
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


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    before: Optional[str] = Query(None, description="이 시각 이전 메시지만 반환 (ISO 8601)"),
    limit: int = Query(30, ge=1, le=100),
) -> dict:
    """cursor 기반 메시지 페이지네이션. before 파라미터로 이전 메시지를 로드한다."""
    user_id = await _resolve_user_id(request, db)

    # 대화 소유권 확인
    conv_result = await db.execute(
        select(Conversation.id).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
    )
    if conv_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")

    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
    )

    if before:
        cursor_dt = datetime.fromisoformat(before)
        query = query.where(Message.created_at < cursor_dt)

    query = query.order_by(Message.created_at.desc()).limit(limit)
    result = await db.execute(query)
    rows = list(reversed(result.scalars().all()))

    messages = [
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
        for msg in rows
    ]

    return {
        "messages": messages,
        "has_more": len(rows) == limit,
    }


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """대화와 관련 메시지를 삭제한다."""
    user_id = await _resolve_user_id(request, db)

    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conv = result.scalar_one_or_none()

    if conv is None:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다")

    await db.delete(conv)  # CASCADE가 관련 messages를 자동 삭제
    await db.commit()

    return {"detail": "대화가 삭제되었습니다"}
