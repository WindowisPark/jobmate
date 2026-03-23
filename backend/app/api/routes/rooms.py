from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db

router = APIRouter()


@router.get("")
async def list_conversations(db: AsyncSession = Depends(get_db)) -> list[dict]:
    # TODO: list user's conversations
    raise NotImplementedError


@router.post("")
async def create_conversation(db: AsyncSession = Depends(get_db)) -> dict:
    # TODO: create new conversation
    raise NotImplementedError


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    # TODO: get conversation with messages
    raise NotImplementedError


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    # TODO: delete conversation
    raise NotImplementedError
