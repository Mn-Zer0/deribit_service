from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import create_engine, create_session_factory
from app.repositories.price_repository import PriceRepository
from app.services.price_service import PriceService

# engine и session_factory создаются на старте приложения
_engine = None
_session_factory = None

def init_db(engine):
    global _engine, _session_factory
    _engine = engine
    _session_factory = create_session_factory(engine)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        yield session

async def get_price_service(
    session: AsyncSession = Depends(get_session),
) -> PriceService:
    repository = PriceRepository(session)
    return PriceService(repository)