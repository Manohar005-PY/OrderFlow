from fastapi import APIRouter,Depends,status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate,UserResponse
from app.services.user_services import create_user
from app.schemas.token import TokenResponse
from app.schemas.user import UserLogin
from app.core.security import create_access_token
from app.services.user_services import authenticate_user

router = APIRouter(prefix="/auth",tags= ["Auth"])

@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def register_user(user_data:UserCreate,db:Session = Depends(get_db)):
    created_user = create_user(db,user_data)
    return created_user

@router.post("/login",response_model=TokenResponse)
def login(data:UserLogin, db:Session = Depends(get_db)):
    
    user = authenticate_user(db,data.email,data.password)
    token = create_access_token(str(user.id))
    return {
        "access_token": token,
        "token_type": "bearer"
    }