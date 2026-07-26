from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from datetime import datetime,timezone,timedelta
from app.core.config import settings
import jwt

ph = PasswordHasher()

def hash_password(password:str) -> str:
    return ph.hash(password)

def verify_password(hashed_password:str, plain_password:str) -> bool:
    try:
        return ph.verify(hashed_password,plain_password)
    except VerifyMismatchError:
        return False

def create_access_token(subject:str) -> str:
    expire = (datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload = {
        "sub": subject,
        "exp": expire,
    }
    token = jwt.encode(payload,settings.JWT_SECRET_KEY,algorithm=settings.JWT_ALGORITHM,)

    return token
