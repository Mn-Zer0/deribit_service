from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from app.config import get_settings

def create_engine():
    settings = get_settings()
    return create_async_engine(settings.DATABASE_URL, echo=False)

def create_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)