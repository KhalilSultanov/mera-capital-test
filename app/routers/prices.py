from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
from app.models import PriceResponse
from app.database import Database

router = APIRouter()


async def get_db(request: Request) -> Database:
    return request.app.state.database


@router.get("/prices", response_model=List[PriceResponse])
async def get_all_prices(
        ticker: str = Query(..., description="Тикер валюты (например, 'btc_usd')"),
        db: Database = Depends(get_db)
):
    prices = await db.get_all_prices(ticker)
    if not prices:
        raise HTTPException(status_code=404, detail="No data found for the specified ticker")
    return prices


@router.get("/latest_price", response_model=PriceResponse)
async def get_latest_price(
        ticker: str = Query(..., description="Тикер валюты (например, 'btc_usd')"),
        db: Database = Depends(get_db)
):
    price = await db.get_latest_price(ticker)
    if not price:
        raise HTTPException(status_code=404, detail="No data found for the specified ticker")
    return price


@router.get("/filtered_prices", response_model=List[PriceResponse])
async def get_filtered_prices(
        ticker: str = Query(..., description="Тикер валюты (например, 'btc_usd')"),
        start: Optional[int] = Query(None, description="Начальный timestamp"),
        end: Optional[int] = Query(None, description="Конечный timestamp"),
        db: Database = Depends(get_db)
):
    prices = await db.get_filtered_prices(ticker, start, end)
    if not prices:
        raise HTTPException(status_code=404, detail="No data found for the specified ticker and/or timeframe")
    return prices
