from __future__ import annotations

from datetime import datetime

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import get_session
from app.main import app
from app.models.price import Base, Price


@pytest_asyncio.fixture
async def db_engine():
    """In-memory SQLite для тестов — не трогает основную БД."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session


@pytest_asyncio.fixture
async def sample_prices(db_session):
    prices = [
        Price(ticker="btc_usd", price=50000.0, timestamp=1700000000),
        Price(ticker="btc_usd", price=51000.0, timestamp=1700000100),
        Price(ticker="eth_usd", price=3000.0, timestamp=1700000000),
    ]
    db_session.add_all(prices)
    await db_session.commit()
    for p in prices:
        await db_session.refresh(p)
    return prices


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_session():
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()