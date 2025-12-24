from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings
from sqlalchemy.engine.url import make_url

if not settings.DB_URL:
    raise RuntimeError("DATABASE_URL is not set")

_url = make_url(settings.DB_URL)
_connect_args = {"check_same_thread": False} if _url.get_backend_name() == "sqlite" else {}

engine = create_engine(
    settings.DB_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    pool_recycle=300
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
