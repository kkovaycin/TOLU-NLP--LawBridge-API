from pydantic import BaseModel, EmailStr
from typing import Optional

class PreferencesRequest(BaseModel):
    user_id: int
    platform: str
    mode: str
    frequency: Optional[str] = None

class PreferencesResponse(BaseModel):
    mode: str
    platform: str
    frequency: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True  # Pydantic v2 uyumu için


