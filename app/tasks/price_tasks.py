import asyncio
import time

import aiohttp
from celery import shared_task

from app.clients.deribit_client import DeribitClient
from app.config import get_settings
from app.database import create_engine, create_session_factory
from app.repositories.price_repository import PriceRepository
from app.services.price_service import PriceService

TICKERS = ["btc_usd", "eth_usd"]


async def _fetch_and_save():
    settings = get_settings()
    engine = create_engine()
    session_factory = create_session_factory(engine)

    async with aiohttp.ClientSession() as http_session:
        client = DeribitClient(http_session, settings.DERIBIT_BASE_URL)
        async with session_factory() as db_session:
            repository = PriceRepository(db_session)
            service = PriceService(repository)

            for ticker in TICKERS:
                price = await client.get_index_price(ticker)
                await service.save_price(ticker, price, int(time.time()))

    await engine.dispose()


@shared_task(name="app.tasks.price_tasks.fetch_and_save_prices")
def fetch_and_save_prices():
    asyncio.run(_fetch_and_save())