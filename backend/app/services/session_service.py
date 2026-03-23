import json
from uuid import UUID

from redis.asyncio import Redis


class SessionService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def create_session(self, user_id: UUID, conversation_id: UUID) -> None:
        key = f"session:{user_id}"
        await self._redis.setex(
            key,
            86400,  # 24h TTL
            json.dumps({
                "user_id": str(user_id),
                "active_conversation_id": str(conversation_id),
            }),
        )

    async def get_session(self, user_id: UUID) -> dict | None:
        key = f"session:{user_id}"
        data = await self._redis.get(key)
        return json.loads(data) if data else None

    async def set_agent_typing(self, conversation_id: UUID, agent_id: str) -> None:
        key = f"typing:{conversation_id}"
        await self._redis.setex(key, 10, agent_id)

    async def set_office_state(self, conversation_id: UUID, state: dict) -> None:
        key = f"office:{conversation_id}"
        await self._redis.setex(key, 30, json.dumps(state))

    async def get_office_state(self, conversation_id: UUID) -> dict | None:
        key = f"office:{conversation_id}"
        data = await self._redis.get(key)
        return json.loads(data) if data else None
