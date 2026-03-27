"""
Pydantic schemas for User
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema"""
    password: str
    role: str = "doctor"


class UserUpdate(BaseModel):
    """User update schema"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """User response schema"""
    id: UUID
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int


class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    """Login response with user info"""
    access_token: str
    token_type: str = "bearer"
    user: 'UserResponse'


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str
    password: str