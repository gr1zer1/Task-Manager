from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    owner_id: int
    assignee_id: Optional[int]
    deadline: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    deadline: Optional[str] = None


class TaskUpdateRequest(BaseModel):
    id: int
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    assignee_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    is_service: bool
    telegram_id: Optional[int] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
