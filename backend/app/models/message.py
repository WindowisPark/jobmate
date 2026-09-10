import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base

# 운영은 Postgres 의 JSONB, 로컬 SQLite 는 JSON 으로 떨어뜨린다.
# 마이그레이션은 JSONB 그대로라 운영 스키마는 바뀌지 않는다. Docker 없이 채팅을 돌리기 위한 장치.
_JSON = JSONB().with_variant(JSON(), "sqlite")



class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (CheckConstraint("sender_type IN ('user', 'agent')", name="ck_sender_type"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_type: Mapped[str] = mapped_column(String(10), nullable=False)
    agent_id: Mapped[str | None] = mapped_column(ForeignKey("agents.id"))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[dict | None] = mapped_column(_JSON)
    tool_results: Mapped[dict | None] = mapped_column(_JSON)
    emotion_tag: Mapped[str | None] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")  # noqa: F821
    agent: Mapped["Agent | None"] = relationship()  # noqa: F821
