from app.core.config import settings
from sqlalchemy import create_engine
from collections.abc import Generator
from sqlalchemy.orm import sessionmaker,Session

engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    bind=engine,
)

def get_db() -> Generator[Session,None,None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_auth_db() -> Generator[Session,None,None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()