from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.price import Price

class PriceRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, ticker: str, price: float, timestamp: int) -> Price:
        obj = Price(ticker=ticker, price=price, timestamp=timestamp)
        self._session.add(obj)
        await self._session.commit()
        await self._session.refresh(obj)
        return obj

    async def get_all_by_ticker(self, ticker: str) -> list[Price]:
        result = await self._session.execute(
            select(Price).where(Price.ticker == ticker).order_by(Price.timestamp)
        )
        return list(result.scalars().all())

    async def get_latest_by_ticker(self, ticker: str) -> Price | None:
        result = await self._session.execute(
            select(Price)
            .where(Price.ticker == ticker)
            .order_by(Price.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_ticker_and_date_range(
        self, ticker: str, from_ts: int, to_ts: int
    ) -> list[Price]:
        result = await self._session.execute(
            select(Price)
            .where(
                Price.ticker == ticker,
                Price.timestamp >= from_ts,
                Price.timestamp <= to_ts,
            )
            .order_by(Price.timestamp)
        )
        return list(result.scalars().all())