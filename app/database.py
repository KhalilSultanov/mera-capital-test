import os
import aiosqlite
from typing import List, Optional, Tuple
from app.models import PriceResponse
from app.config import settings
import logging

LOG = logging.getLogger(__name__)


class Database:
    def __init__(self, db_url: str = settings.database_url):
        self.db_url = db_url
        self.conn = None

    async def initialize(self):
        os.makedirs(os.path.dirname(self.db_url), exist_ok=True)
        async with aiosqlite.connect(self.db_url) as db:
            LOG.info("Connected to database.")
            await db.execute('''
                CREATE TABLE IF NOT EXISTS crypto_prices (
                    ticker TEXT,
                    price REAL,
                    timestamp INTEGER
                )
            ''')
            LOG.info("Table 'crypto_prices' ensured.")
            await db.commit()
            LOG.info("Database initialization complete.")

    async def insert_price(self, ticker: str, price: float, timestamp: int):
        if price < 0:
            LOG.error(f"Attempted to insert negative price: {price}")
            raise ValueError("Price cannot be negative.")

        async with aiosqlite.connect(self.db_url) as db:
            await db.execute(
                'INSERT INTO crypto_prices (ticker, price, timestamp) VALUES (?, ?, ?)',
                (ticker, price, timestamp)
            )
            await db.commit()
            LOG.info(f"Inserted price for {ticker}: {price} at {timestamp}")

    async def get_all_prices(self, ticker: str) -> List[PriceResponse]:
        async with aiosqlite.connect(self.db_url) as db:
            async with db.execute(
                    'SELECT ticker, price, timestamp FROM crypto_prices WHERE ticker = ?',
                    (ticker,)
            ) as cursor:
                rows = await cursor.fetchall()
        return [PriceResponse(ticker=row[0], price=row[1], timestamp=row[2]) for row in rows]

    async def get_latest_price(self, ticker: str) -> Optional[PriceResponse]:
        async with aiosqlite.connect(self.db_url) as db:
            async with db.execute(
                    '''SELECT ticker, price, timestamp FROM crypto_prices 
                       WHERE ticker = ? ORDER BY timestamp DESC LIMIT 1''',
                    (ticker,)
            ) as cursor:
                row = await cursor.fetchone()
        if row:
            return PriceResponse(ticker=row[0], price=row[1], timestamp=row[2])
        return None

    async def get_filtered_prices(self, ticker: str, start: Optional[int], end: Optional[int]) -> List[PriceResponse]:
        async with aiosqlite.connect(self.db_url) as db:
            if start and end:
                query = '''
                    SELECT ticker, price, timestamp FROM crypto_prices 
                    WHERE ticker = ? AND timestamp BETWEEN ? AND ?
                '''
                params: Tuple = (ticker, start, end)
            else:
                query = 'SELECT ticker, price, timestamp FROM crypto_prices WHERE ticker = ?'
                params = (ticker,)
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
        return [PriceResponse(ticker=row[0], price=row[1], timestamp=row[2]) for row in rows]

    async def close(self):
        if self.conn:
            await self.conn.close()
