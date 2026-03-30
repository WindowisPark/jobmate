import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Integer, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class JobPreference(Base):
    __tablename__ = "user_job_preferences"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    job_field: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(100))
    career_level: Mapped[str | None] = mapped_column(String(50))
    keywords: Mapped[list] = mapped_column(JSONB, default=list)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    company_size: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship()  # noqa: F821
