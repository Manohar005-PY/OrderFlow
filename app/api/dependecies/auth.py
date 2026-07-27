from  fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException,status,Depends
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token:str = Depends(oauth2_scheme), db:Session = Depends(get_db)) -> User:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid token")
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Invalid Token",)

    user = db.get(User,int(user_id))

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="user not found")

    return user

def get_current_active_user(current_user:User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive User")

    return current_user

def required_roles(*roles:UserRole):

    def role_cheacker(current_user: User = Depends(get_current_active_user)) -> User:

        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Insufficient Permission")

        return current_user
    return role_cheacker