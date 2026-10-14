from fastapi import APIRouter, Depends, HTTPException, Query
from app.schemas.price import PriceResponse
from app.services.price_service import PriceService
from app.api.dependencies import get_price_service

router = APIRouter(prefix="/prices", tags=["prices"])

@router.get("/", response_model=list[PriceResponse])
async def get_all_prices(
    ticker: str = Query(..., description="btc_usd или eth_usd"),
    service: PriceService = Depends(get_price_service),
):
    return await service.get_all_prices(ticker)

@router.get("/latest", response_model=PriceResponse)
async def get_latest_price(
    ticker: str = Query(..., description="btc_usd или eth_usd"),
    service: PriceService = Depends(get_price_service),
):
    price = await service.get_latest_price(ticker)
    if price is None:
        raise HTTPException(status_code=404, detail="No data for this ticker")
    return price

@router.get("/by-date", response_model=list[PriceResponse])
async def get_prices_by_date(
    ticker: str = Query(...),
    from_ts: int = Query(..., description="UNIX timestamp начала"),
    to_ts: int = Query(..., description="UNIX timestamp конца"),
    service: PriceService = Depends(get_price_service),
):
    return await service.get_prices_by_date(ticker, from_ts, to_ts)