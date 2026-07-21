from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
class UserCreate(BaseModel):
    email:EmailStr
    password:str = Field(min_length=8, max_length=128)
    fullname:str = Field(min_length=1,max_length=100)

class UserResponse(BaseModel):
    id:int
    email:EmailStr
    full_name:str
    is_active:bool
    created_at:datetime

    class Config:
        from_attributes = True