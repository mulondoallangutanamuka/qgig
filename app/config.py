import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    _raw_db_url = os.getenv("DATABASE_URL")
    if not _raw_db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    
    if _raw_db_url.startswith("postgres://"):
        # Render and some providers still use the deprecated scheme.
        # SQLAlchemy expects postgresql:// (or postgresql+psycopg2://).
        DB_URL = _raw_db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif _raw_db_url.startswith("postgresql://"):
        # Add psycopg2 driver if not specified
        DB_URL = _raw_db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    else:
        DB_URL = _raw_db_url
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    PESAPAL_CONSUMER_KEY = os.getenv("PESAPAL_CONSUMER_KEY")
    PESAPAL_CONSUMER_SECRET = os.getenv("PESAPAL_CONSUMER_SECRET")
    PESAPAL_CALLBACK_URL = os.getenv("PESAPAL_CALLBACK_URL")
    PESAPAL_BASE_URL = os.getenv("PESAPAL_BASE_URL", "https://cybqa.pesapal.com/pesapalv3/api")

settings = Settings()
