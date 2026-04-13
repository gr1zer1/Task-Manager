from pydantic import BaseModel, ConfigDict, EmailStr


class UserSchema(BaseModel):
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: str
    is_active: bool


class TaskSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    title: str
    description: str | None = None
    is_completed: bool = False


class TaskResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    description: str | None = None
    is_completed: bool
    user_id: int
