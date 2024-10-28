from pydantic import BaseModel, ConfigDict


class PriceResponse(BaseModel):
    ticker: str
    price: float
    timestamp: int

    model_config = ConfigDict(from_attributes=True)
