import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.routes import auth, chat, rooms, users

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    logger.info("JobMate starting up")
    yield
    logger.info("JobMate shutting down")


app = FastAPI(
    title=settings.app_name,
    description="취준생 멘탈 케어 멀티에이전트 챗봇",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # HTTPException은 FastAPI가 자체 처리하도록 통과
    if isinstance(exc, HTTPException):
        raise exc
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 내부 오류가 발생했습니다"},
    )


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(rooms.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(chat.router, prefix="/ws", tags=["chat"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
