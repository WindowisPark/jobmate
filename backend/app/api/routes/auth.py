from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.user import UserCreate, UserLogin, TokenPair

router = APIRouter()


@router.post("/register", response_model=TokenPair)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)) -> TokenPair:
    # TODO: implement registration
    raise NotImplementedError


@router.post("/login", response_model=TokenPair)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)) -> TokenPair:
    # TODO: implement login
    raise NotImplementedError


@router.post("/refresh", response_model=TokenPair)
async def refresh_token() -> TokenPair:
    # TODO: implement token refresh
    raise NotImplementedError
