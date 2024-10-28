import asyncio
import time
import aiohttp
import logging
from typing import Optional
from app.config import settings
from app.database import Database

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PriceFetcher:
    def __init__(self, db: Database, interval: int = settings.fetch_interval):
        self.db = db
        self.interval = interval
        self.url_btc = "https://www.deribit.com/api/v2/public/get_index_price?index_name=btc_usd"
        self.url_eth = "https://www.deribit.com/api/v2/public/get_index_price?index_name=eth_usd"
        self.session = aiohttp.ClientSession()
        self.task: Optional[asyncio.Task] = None

    async def fetch_price(self, url: str) -> Optional[float]:
        try:
            async with self.session.get(url) as response:
                data = await response.json()
                price = data.get('result', {}).get('index_price')
                if price is None:
                    logger.warning(f"Price not found in response from {url}")
                return price
        except Exception as e:
            logger.error(f"Error fetching price from {url}: {e}")
            return None

    async def fetch_prices_loop(self):
        while True:
            try:
                btc_price = await self.fetch_price(self.url_btc)
                eth_price = await self.fetch_price(self.url_eth)

                if btc_price is not None and eth_price is not None:
                    timestamp = int(time.time())
                    await self.db.insert_price("btc_usd", btc_price, timestamp)
                    await self.db.insert_price("eth_usd", eth_price, timestamp)
                    logger.info(f"Saved btc_usd: {btc_price}, eth_usd: {eth_price} at {timestamp}")
                else:
                    logger.warning("Failed to fetch one or both prices.")

            except Exception as e:
                logger.error(f"Error in fetch_prices_loop: {e}")

            await asyncio.sleep(self.interval)

    async def start(self):
        self.task = asyncio.create_task(self.fetch_prices_loop())
        logger.info("PriceFetcher started.")

    async def shutdown(self):
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                logger.info("PriceFetcher task cancelled.")
        await self.session.close()
        logger.info("PriceFetcher shutdown.")
