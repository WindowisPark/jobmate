from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from passlib.context import CryptContext
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_db, get_redis
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserOut
from app.api.middleware.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_refresh_token,
    save_refresh_token,
    verify_refresh_token,
)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

COOKIE_OPTS: dict = {
    "httponly": True,
    "samesite": "lax",
    "secure": False,  # dev: False, prod: True
}


def _set_auth_cookies(response: Response, access: str, refresh: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
        **COOKIE_OPTS,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        max_age=settings.refresh_token_expire_days * 86400,
        path="/api/auth",
        **COOKIE_OPTS,
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth")


@router.post("/check-email")
async def check_email(
    body: UserLogin,  # email 필드만 사용
    db: AsyncSession = Depends(get_db),
) -> dict:
    """이메일 중복 확인."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다")
    return {"available": True}


@router.post("/register", response_model=UserOut)
async def register(
    body: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> UserOut:
    """회원가입 후 자동 로그인."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="이미 등록된 이메일입니다")

    user = User(
        email=body.email,
        password_hash=pwd_context.hash(body.password),
        nickname=body.nickname,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    await save_refresh_token(redis, user.id, refresh)
    _set_auth_cookies(response, access, refresh)

    return UserOut(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


@router.post("/login", response_model=UserOut)
async def login(
    body: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> UserOut:
    """로그인 후 쿠키에 토큰 설정."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    await save_refresh_token(redis, user.id, refresh)
    _set_auth_cookies(response, access, refresh)

    return UserOut(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


@router.post("/refresh", response_model=UserOut)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> UserOut:
    """Refresh Token Rotation으로 새 토큰 쌍 발급."""
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token이 없습니다")

    payload = decode_token(token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="유효하지 않은 refresh token입니다")

    user_id = UUID(payload["sub"])

    if not await verify_refresh_token(redis, user_id, token):
        await revoke_refresh_token(redis, user_id)
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh token이 재사용되었습니다. 다시 로그인해주세요.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")

    new_access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)
    await save_refresh_token(redis, user.id, new_refresh)
    _set_auth_cookies(response, new_access, new_refresh)

    return UserOut(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    redis: Redis = Depends(get_redis),
) -> dict:
    """로그아웃: 쿠키 삭제 + Redis refresh token 무효화."""
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = decode_token(token)
            user_id = UUID(payload["sub"])
            await revoke_refresh_token(redis, user_id)
        except Exception:
            pass

    _clear_auth_cookies(response)
    return {"detail": "로그아웃되었습니다"}


@router.get("/me", response_model=UserOut)
async def get_me(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserOut:
    """현재 로그인된 유저 정보 반환. 쿠키 유효성 검증용으로도 사용."""
    from app.api.middleware.auth import get_current_user_id
    user_id = await get_current_user_id(request)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")

    return UserOut(
        id=user.id,
        email=user.email,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        created_at=user.created_at,
    )
