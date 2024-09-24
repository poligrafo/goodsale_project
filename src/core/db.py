from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.core.models import Base
from src.core.settings import settings

DATABASE_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
    f"@{settings.DATABASE_HOST}:{settings.DATABASE_PORT}/{settings.POSTGRES_DB}"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
