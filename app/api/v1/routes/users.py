from fastapi import APIRouter, Depends

from app.api.dependecies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse

user_router = APIRouter(prefix="/users",tags=["Users"])

@user_router.get("/me",response_model=UserResponse)
def get_me(current_user:User = Depends(get_current_user)):
    return current_user