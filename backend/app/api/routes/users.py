from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(db: AsyncSession = Depends(get_db)) -> UserOut:
    # TODO: implement with JWT auth dependency
    raise NotImplementedError


@router.patch("/me", response_model=UserOut)
async def update_me(db: AsyncSession = Depends(get_db)) -> UserOut:
    # TODO: implement profile update
    raise NotImplementedError
