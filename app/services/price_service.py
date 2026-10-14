from app.repositories.price_repository import PriceRepository
from app.models.price import Price

class PriceService:
    def __init__(self, repository: PriceRepository):
        self._repository = repository

    async def get_all_prices(self, ticker: str) -> list[Price]:
        return await self._repository.get_all_by_ticker(ticker)

    async def get_latest_price(self, ticker: str) -> Price | None:
        return await self._repository.get_latest_by_ticker(ticker)

    async def get_prices_by_date(
        self, ticker: str, from_ts: int, to_ts: int
    ) -> list[Price]:
        return await self._repository.get_by_ticker_and_date_range(ticker, from_ts, to_ts)

    async def save_price(self, ticker: str, price: float, timestamp: int) -> Price:
        return await self._repository.create(ticker, price, timestamp)