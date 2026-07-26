from sqlalchemy.orm import Session
from fastapi import HTTPException,status
from app.schemas.user import UserCreate
from app.models.user import User
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.security import hash_password
from app.core.security import verify_password

def create_user(db:Session, user:UserCreate) -> User:
    existing_user = db.scalar(select(User).where(User.email == user.email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email_already_register")


    user_data = User(email = user.email, 
                     hashed_password = hash_password(user.password),
                     full_name = user.fullname)
    
    db.add(user_data)

    try:
        db.commit()
        db.refresh(user_data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email_already_register")
    
    return user_data

def authenticate_user(db:Session,email:str,password:str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail="Incorrect Email or Password")

    if not verify_password(user.hashed_password,password):
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED,detail="Incorrect Email or Password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="User account is not active")

    return user