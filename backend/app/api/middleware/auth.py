import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from redis.asyncio import Redis

from app.config import settings
from app.dependencies import get_redis


def create_access_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode(
        {"sub": str(user_id), "exp": expire, "type": "refresh", "jti": secrets.token_hex(16)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict:
    """JWT 토큰을 디코딩한다. 실패 시 HTTPException."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="유효하지 않은 토큰입니다")


# --- Redis Refresh Token 관리 ---

REFRESH_KEY_PREFIX = "refresh:"
REFRESH_TTL = settings.refresh_token_expire_days * 86400  # seconds


async def save_refresh_token(redis: Redis, user_id: UUID, token: str) -> None:
    """Refresh token을 Redis에 저장한다."""
    payload = decode_token(token)
    jti = payload.get("jti", "")
    key = f"{REFRESH_KEY_PREFIX}{user_id}"
    await redis.set(key, jti, ex=REFRESH_TTL)


async def verify_refresh_token(redis: Redis, user_id: UUID, token: str) -> bool:
    """Redis에 저장된 refresh token과 일치하는지 확인한다."""
    payload = decode_token(token)
    jti = payload.get("jti", "")
    key = f"{REFRESH_KEY_PREFIX}{user_id}"
    stored_jti = await redis.get(key)
    return stored_jti == jti


async def revoke_refresh_token(redis: Redis, user_id: UUID) -> None:
    """Refresh token을 Redis에서 삭제한다 (로그아웃)."""
    key = f"{REFRESH_KEY_PREFIX}{user_id}"
    await redis.delete(key)


# --- FastAPI Dependencies ---

async def get_current_user_id(request: Request) -> UUID:
    """쿠키에서 access_token을 읽어 user_id를 반환한다."""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다")

    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return UUID(user_id)


async def get_optional_user_id(request: Request) -> UUID | None:
    """쿠키에서 access_token을 읽되, 없으면 None (게스트 모드)."""
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        return UUID(user_id) if user_id else None
    except (JWTError, ValueError):
        return None


def get_ws_user_id(websocket) -> UUID | None:
    """WebSocket 연결의 쿠키에서 user_id를 추출한다. 없으면 None (게스트)."""
    token = websocket.cookies.get("access_token")
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        return UUID(user_id) if user_id else None
    except (JWTError, ValueError):
        return None
