import pytest
import asyncio
import logging
from app.services import PriceFetcher

logging.basicConfig(level=logging.INFO)


@pytest.mark.asyncio
async def test_price_fetcher_integration(test_db):
    """
    Интеграционный тест для проверки взаимодействия PriceFetcher и Database.
    """
    fetcher = PriceFetcher(db=test_db, interval=0.1)

    task = asyncio.create_task(fetcher.fetch_prices_loop())

    await asyncio.sleep(1)

    prices_btc = await test_db.get_all_prices("btc_usd")
    prices_eth = await test_db.get_all_prices("eth_usd")

    assert len(prices_btc) > 0, "Ожидается, что данные BTC будут сохранены в базу"
    assert len(prices_eth) > 0, "Ожидается, что данные ETH будут сохранены в базу"

    task.cancel()
    await fetcher.shutdown()
    await asyncio.sleep(0.1)
