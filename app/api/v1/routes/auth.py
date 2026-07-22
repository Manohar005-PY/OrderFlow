from fastapi import APIRouter,Depends,status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate,UserResponse
from app.services.user_services import create_user

router = APIRouter(prefix="/auth",tags= ["Auth"])

@router.post("/register",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def register_user(user_data:UserCreate,db:Session = Depends(get_db)):
    created_user = create_user(db,user_data)
    return created_user