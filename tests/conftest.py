import os
import shutil
import tempfile

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import Database
from unittest.mock import AsyncMock
from app.routers.prices import get_db
from app.services import PriceFetcher


@pytest.fixture
async def mock_db():
    """
    Фикстура для создания мока базы данных.
    """
    mock = AsyncMock(spec=Database)
    mock.get_all_prices.return_value = []
    mock.get_latest_price.return_value = None
    mock.get_filtered_prices.return_value = []
    return mock


@pytest.fixture
async def client(mock_db):
    """
    Фикстура для создания тестового клиента с переопределённой зависимостью Database.
    """

    async def override_get_db():
        return mock_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
async def test_db():
    """
    Фикстура для создания временной базы данных.
    """
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test_crypto_data.db")
    db = Database(db_url=temp_db_path)
    await db.initialize()
    yield db
    await db.close()
    shutil.rmtree(temp_dir)


@pytest.fixture
async def price_fetcher(test_db):
    """
    Фикстура для создания экземпляра PriceFetcher.
    """
    fetcher = PriceFetcher(db=test_db, interval=0.1)
    yield fetcher
    await fetcher.shutdown()
