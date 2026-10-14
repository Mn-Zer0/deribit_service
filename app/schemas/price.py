from pydantic import BaseModel, ConfigDict

class PriceBase(BaseModel):
    ticker: str
    price: float
    timestamp: int

class PriceResponse(PriceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int