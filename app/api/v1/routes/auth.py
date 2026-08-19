from fastapi import APIRouter,Depends,status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.db.session import get_auth_db
# from app.models.user import User
from app.schemas.user import UserCreate,UserResponse
from app.services.user_services import create_user
# from app.schemas.token import TokenResponse
# from app.schemas.user import UserLogin
from app.core.security import create_access_token
from app.services.user_services import authenticate_user

auth_router = APIRouter(prefix="/auth",tags= ["Auth"])

@auth_router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def register_user(user_data:UserCreate,db:Session = Depends(get_auth_db)):
    created_user = create_user(db,user_data)
    return created_user

@auth_router.post("/login")
def login(form_data:OAuth2PasswordRequestForm = Depends(), db:Session = Depends(get_auth_db)):

    user = authenticate_user(db,form_data.username,form_data.password)
    token = create_access_token(str(user.id))
    return {
        "access_token": token,
        "token_type": "bearer"
    }