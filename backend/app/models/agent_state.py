import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, SmallInteger, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(100), nullable=False)
    personality: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class UserEmotionLog(Base):
    __tablename__ = "user_emotion_logs"
    __table_args__ = (
        CheckConstraint("intensity BETWEEN 1 AND 5", name="ck_intensity_range"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("conversations.id"))
    emotion: Mapped[str] = mapped_column(String(20), nullable=False)
    intensity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    context: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    user: Mapped["User"] = relationship(back_populates="emotion_logs")  # noqa: F821
