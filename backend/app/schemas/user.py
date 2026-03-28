import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    nickname: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다")
        if len(v) > 60:
            raise ValueError("비밀번호는 60자 이내여야 합니다")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("비밀번호에 영문자를 포함해야 합니다")
        if not re.search(r"\d", v):
            raise ValueError("비밀번호에 숫자를 포함해야 합니다")
        return v

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, v: str) -> str:
        if len(v.strip()) < 2:
            raise ValueError("닉네임은 2자 이상이어야 합니다")
        if len(v) > 50:
            raise ValueError("닉네임은 50자 이내여야 합니다")
        return v.strip()


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: UUID
    email: str
    nickname: str
    avatar_url: str | None = None
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
