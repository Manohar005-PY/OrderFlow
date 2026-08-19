from fastapi import APIRouter, Depends
from app.api.dependecies.auth import required_roles
from app.models.enums import UserRole
from app.api.dependecies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserResponse

user_router = APIRouter(prefix="/users",tags=["Users"])

@user_router.get("/me",response_model=UserResponse)
def get_me(current_user:User = Depends(get_current_active_user)):
    return current_user

@user_router.get("/admin-test")
def admin_test(
    current_user = Depends(
        required_roles(UserRole.ADMIN)
    )
):
    return {"message": "Welcome Admin"}