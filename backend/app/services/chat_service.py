import uuid
from datetime import datetime

from sqlalchemy import select, update as sa_update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.graph import build_graph
from app.agents.state import JobMateState
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User

# JWT 구현 전까지 사용할 anonymous 유저 고정 ID
ANONYMOUS_USER_ID = uuid.uuid5(uuid.NAMESPACE_URL, "anonymous")


async def ensure_anonymous_user(db: AsyncSession) -> uuid.UUID:
    """anonymous 유저가 없으면 생성한다. JWT 인증 구현 후 제거."""
    result = await db.execute(
        select(User).where(User.id == ANONYMOUS_USER_ID)
    )
    if result.scalar_one_or_none() is None:
        user = User(
            id=ANONYMOUS_USER_ID,
            email="anonymous@jobmate.local",
            password_hash="no-auth",
            nickname="취준생",
        )
        db.add(user)
        await db.flush()
    return ANONYMOUS_USER_ID


async def get_or_create_conversation(
    db: AsyncSession,
    conversation_id: str,
    user_id: str,
) -> Conversation:
    """conversation_id로 대화를 조회하거나, 없으면 새로 생성한다.

    INSERT...ON CONFLICT DO NOTHING 패턴으로 race condition을 방지한다.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
    except ValueError:
        conv_uuid = uuid.uuid5(uuid.NAMESPACE_URL, conversation_id)

    # 먼저 조회 시도 (대부분의 경우 이미 존재)
    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_uuid)
    )
    conv = result.scalar_one_or_none()
    if conv is not None:
        return conv

    # 없으면 UPSERT로 안전하게 생성
    user_uuid = await ensure_anonymous_user(db)
    now = datetime.utcnow()

    stmt = pg_insert(Conversation).values(
        id=conv_uuid,
        user_id=user_uuid,
        title=None,
        created_at=now,
        updated_at=now,
    ).on_conflict_do_nothing(index_elements=["id"])
    await db.execute(stmt)
    await db.flush()

    # INSERT 성공 또는 충돌 무시 후, 확정된 행을 다시 조회
    result = await db.execute(
        select(Conversation).where(Conversation.id == conv_uuid)
    )
    return result.scalar_one()


async def save_user_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    content: str,
    emotion_tag: str | None = None,
) -> Message:
    """사용자 메시지를 DB에 저장한다."""
    msg = Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        sender_type="user",
        agent_id=None,
        content=content,
        tool_calls=None,
        tool_results=None,
        emotion_tag=emotion_tag,
        created_at=datetime.utcnow(),
    )
    db.add(msg)
    await db.flush()
    return msg


async def save_agent_message(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    agent_id: str,
    content: str,
    tool_calls: list[dict] | None = None,
    emotion_tag: str | None = None,
) -> Message:
    """에이전트 응답을 DB에 저장한다."""
    tool_calls_json = None
    tool_results_json = None

    if tool_calls:
        tool_calls_json = [{"name": tc["name"], "args": tc["args"]} for tc in tool_calls]
        tool_results_json = [{"name": tc["name"], "result": tc["result"]} for tc in tool_calls]

    msg = Message(
        id=uuid.uuid4(),
        conversation_id=conversation_id,
        sender_type="agent",
        agent_id=agent_id,
        content=content,
        tool_calls=tool_calls_json,
        tool_results=tool_results_json,
        emotion_tag=emotion_tag,
        created_at=datetime.utcnow(),
    )
    db.add(msg)
    await db.flush()
    return msg


async def load_conversation_history(
    db: AsyncSession,
    conversation_id: uuid.UUID,
    limit: int = 20,
) -> list[dict]:
    """대화 히스토리를 LLM 메시지 형식으로 로드한다.

    Returns:
        [{"role": "user"|"assistant", "content": str, "name": str|None}, ...]
    """
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    rows = list(reversed(result.scalars().all()))

    history: list[dict] = []
    for msg in rows:
        if msg.sender_type == "user":
            history.append({
                "role": "user",
                "content": msg.content,
            })
        else:
            # 에이전트 이름을 포함해서 누가 말했는지 구분
            history.append({
                "role": "assistant",
                "content": msg.content,
                "agent_id": msg.agent_id,
            })

    return history


async def process_user_message(
    db: AsyncSession,
    user_id: str,
    conversation_id: str,
    content: str,
) -> list[dict]:
    """사용자 메시지를 처리하고 에이전트 응답을 생성한다."""
    # 1. 대화방 확보
    conv = await get_or_create_conversation(db, conversation_id, user_id)

    # 2. 이전 대화 히스토리 로드
    history = await load_conversation_history(db, conv.id)

    # 3. 사용자 메시지 저장
    await save_user_message(db, conv.id, content)

    # 4. LangGraph 실행
    graph = build_graph()
    initial_state: JobMateState = {
        "messages": [],
        "user_message": content,
        "conversation_history": history,
        "emotion": "",
        "emotion_intensity": 0,
        "intent": "",
        "active_agents": [],
        "agent_responses": [],
        "conversation_id": str(conv.id),
        "user_id": user_id,
    }

    result = await graph.ainvoke(initial_state)
    responses = result.get("agent_responses", [])

    # 5. 에이전트 응답 저장
    emotion = result.get("emotion", "")
    for resp in responses:
        await save_agent_message(
            db,
            conv.id,
            agent_id=resp["agent_id"],
            content=resp["content"],
            tool_calls=resp.get("tool_calls"),
            emotion_tag=emotion or None,
        )

    # 6. 대화 제목 자동 생성 (첫 메시지 — atomic UPDATE로 경쟁 방지)
    title_text = content[:50] + ("..." if len(content) > 50 else "")
    await db.execute(
        sa_update(Conversation)
        .where(Conversation.id == conv.id, Conversation.title.is_(None))
        .values(title=title_text, updated_at=datetime.utcnow())
    )

    await db.commit()
    return responses
