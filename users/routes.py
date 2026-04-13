from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import (
    db_helper,
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    UserModel,
    config
)
from tasks.schemas import UserSchema, UserResponseSchema

SessionDep = Annotated[AsyncSession, Depends(db_helper.get_session)]

router = APIRouter(tags=["Users"])


@router.post("/register", response_model=UserResponseSchema)
async def register(user: UserSchema, session: SessionDep) -> UserResponseSchema:
    stmt = select(UserModel).where(UserModel.email == user.email)
    existing_user = await session.execute(stmt)
    
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    new_user = UserModel(
        email=user.email,
        password=hash_password(user.password),
    )
    
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    return new_user


@router.post("/login")
async def login(
    response: Response,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: SessionDep,
) -> dict:
    stmt = select(UserModel).where(UserModel.email == form.username)
    user = await session.execute(stmt)
    user_data = user.scalar_one_or_none()
    
    if not user_data or not verify_password(form.password, user_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = create_access_token(user_data.id)
    refresh_token = create_refresh_token(user_data.id)
    
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=config.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        samesite="lax",
        secure=True,
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserResponseSchema.model_validate(user_data),
    }


@router.get("", response_model=List[UserResponseSchema])
async def get_all_users(session: SessionDep) -> List[UserResponseSchema]:
    stmt = select(UserModel)
    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_user(user_id: int, session: SessionDep) -> UserResponseSchema:
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
