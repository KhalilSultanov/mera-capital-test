import asyncio
import pytest
from app.database import Database
import os


@pytest.fixture
async def db(tmp_path):
    """
    Фикстура для создания временной базы данных и инициализации таблицы.
    """
    db_path = os.path.join(tmp_path, "test_crypto_data.db")
    test_db = Database(db_url=db_path)
    await test_db.initialize()
    yield test_db
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.mark.asyncio
async def test_insert_and_get_all_prices(db):
    """
    Тестирует вставку и получение всех цен для конкретного тикера.
    """
    await db.insert_price("btc_usd", 50000.0, 1625077800)
    await db.insert_price("btc_usd", 50500.0, 1625078400)

    prices = await db.get_all_prices("btc_usd")
    assert len(prices) == 2
    assert prices[0].ticker == "btc_usd"
    assert prices[0].price == 50000.0
    assert prices[0].timestamp == 1625077800

    assert prices[1].ticker == "btc_usd"
    assert prices[1].price == 50500.0
    assert prices[1].timestamp == 1625078400


@pytest.mark.asyncio
async def test_get_latest_price(db):
    """
    Тестирует получение последней цены для указанного тикера.
    """
    await db.insert_price("btc_usd", 50000.0, 1625077800)
    await db.insert_price("btc_usd", 50500.0, 1625078400)

    latest_price = await db.get_latest_price("btc_usd")
    assert latest_price is not None
    assert latest_price.price == 50500.0
    assert latest_price.timestamp == 1625078400


@pytest.mark.asyncio
async def test_get_latest_price_not_found(db):
    """
    Тестирует поведение метода получения последней цены, когда для указанного тикера нет записей.
    """
    latest_price = await db.get_latest_price("unknown_ticker")
    assert latest_price is None


@pytest.mark.asyncio
async def test_get_filtered_prices(db):
    """
    Тестирует фильтрацию цен по диапазону временных меток для указанного тикера.
    """
    await db.insert_price("btc_usd", 50000.0, 1625077800)
    await db.insert_price("btc_usd", 50500.0, 1625078400)
    await db.insert_price("btc_usd", 51000.0, 1625079000)

    prices = await db.get_filtered_prices("btc_usd", 1625078000, 1625079000)
    assert len(prices) == 2
    assert prices[0].price == 50500.0
    assert prices[1].price == 51000.0


@pytest.mark.asyncio
async def test_insert_negative_price(db):
    """
    Тестирует, что вставка отрицательной цены вызывает исключение ValueError.
    """
    with pytest.raises(ValueError) as exc_info:
        await db.insert_price("btc_usd", -50000.0, 1625077800)

    assert str(exc_info.value) == "Price cannot be negative.", "Ожидалось исключение при вставке отрицательной цены."


@pytest.mark.asyncio
async def test_insert_invalid_data_type(db):
    """
    Тестирует, что вставка данных с неправильным типом для цены вызывает исключение TypeError или ValueError.
    """
    with pytest.raises(TypeError):
        await db.insert_price("btc_usd", "fifty thousand", 1625077800)


@pytest.mark.asyncio
async def test_get_all_prices_empty(db):
    """
    Тестирует, что запрос всех цен для тикера без записей возвращает пустой список.
    """
    prices = await db.get_all_prices("unknown_ticker")
    assert prices == [], "Ожидался пустой список для тикера без записей."


@pytest.mark.asyncio
async def test_get_filtered_prices_invalid_range(db):
    """
    Тестирует, что фильтрация с некорректным диапазоном временных меток (start > end) возвращает пустой список.
    """
    await db.insert_price("btc_usd", 50000.0, 1625077800)
    await db.insert_price("btc_usd", 50500.0, 1625078400)

    prices = await db.get_filtered_prices("btc_usd", 1625079000, 1625078000)

    assert prices == [], "Ожидался пустой список при некорректном диапазоне временных меток."


@pytest.mark.asyncio
async def test_get_filtered_prices_negative_timestamps(db):
    """
    Тестирует, что фильтрация с отрицательными временными метками корректно возвращает соответствующие записи.
    """
    await db.insert_price("btc_usd", 50000.0, 1625077800)

    prices = await db.get_filtered_prices("btc_usd", -1000, 1625078000)

    assert len(prices) == 1, "Ожидалась одна запись в результате фильтрации."
    assert prices[0].ticker == "btc_usd"
    assert prices[0].price == 50000.0
    assert prices[0].timestamp == 1625077800


@pytest.mark.asyncio
async def test_multiple_tickers(db):
    """
    Тестирует вставку и получение данных для нескольких тикеров, обеспечивая изоляцию данных.
    """
    await db.insert_price("btc_usd", 50000.0, 1625077800)
    await db.insert_price("btc_usd", 50500.0, 1625078400)
    await db.insert_price("eth_usd", 2500.0, 1625077800)
    await db.insert_price("eth_usd", 2550.0, 1625078400)

    btc_prices = await db.get_all_prices("btc_usd")
    assert len(btc_prices) == 2
    assert btc_prices[0].price == 50000.0
    assert btc_prices[1].price == 50500.0

    eth_prices = await db.get_all_prices("eth_usd")
    assert len(eth_prices) == 2
    assert eth_prices[0].price == 2500.0
    assert eth_prices[1].price == 2550.0


@pytest.mark.asyncio
async def test_concurrent_operations(db):
    """
    Тестирует одновременные вставки и запросы к базе данных, обеспечивая корректную обработку конкурентных операций.
    """

    async def insert_prices():
        for i in range(100):
            await db.insert_price("btc_usd", 50000.0 + i, 1625077800 + i)

    async def get_latest_prices():
        latest_prices = []
        for _ in range(100):
            price = await db.get_latest_price("btc_usd")
            if price:
                latest_prices.append(price.price)
        return latest_prices

    insert_task = asyncio.create_task(insert_prices())
    get_task = asyncio.create_task(get_latest_prices())

    await asyncio.gather(insert_task, get_task)

    prices = await db.get_all_prices("btc_usd")
    assert len(prices) == 100, f"Ожидалось 100 записей, получено {len(prices)}"

    expected_prices = [50000.0 + i for i in range(100)]
    actual_prices = sorted([price.price for price in prices])
    assert actual_prices == expected_prices, "Цены не соответствуют ожидаемым значениям."


@pytest.mark.asyncio
async def test_insert_duplicate_prices(db):
    """
    Тестирует вставку дубликатов и проверяет, что они корректно сохраняются в базе данных.
    """
    await db.insert_price("btc_usd", 50000.0, 1625077800)
    await db.insert_price("btc_usd", 50000.0, 1625077800)

    prices = await db.get_all_prices("btc_usd")
    assert len(prices) == 2, f"Ожидалось 2 записи, получено {len(prices)}"
    assert prices[0].price == 50000.0
    assert prices[1].price == 50000.0


@pytest.mark.asyncio
async def test_insert_large_values(db):
    """
    Тестирует вставку и получение больших значений цены и временных меток, обеспечивая корректную обработку больших чисел.
    """
    large_price = 1e15
    large_timestamp = 9999999999

    await db.insert_price("btc_usd", large_price, large_timestamp)

    latest_price = await db.get_latest_price("btc_usd")
    assert latest_price is not None, "Ожидалась запись с большой ценой."
    assert latest_price.price == large_price, f"Ожидалась цена {large_price}, получено {latest_price.price}"
    assert latest_price.timestamp == large_timestamp, f"Ожидалась временная метка {large_timestamp}, получено {latest_price.timestamp}"


@pytest.mark.asyncio
async def test_multiple_tickers_separation(db):
    """
    Тестирует, что данные для разных тикеров не смешиваются и правильно разделяются.
    """
    await db.insert_price("btc_usd", 50000.0, 1625077800)
    await db.insert_price("eth_usd", 2500.0, 1625077800)
    await db.insert_price("btc_usd", 50500.0, 1625078400)
    await db.insert_price("eth_usd", 2550.0, 1625078400)

    btc_prices = await db.get_all_prices("btc_usd")
    assert len(btc_prices) == 2, f"Ожидалось 2 записи для btc_usd, получено {len(btc_prices)}"

    eth_prices = await db.get_all_prices("eth_usd")
    assert len(eth_prices) == 2, f"Ожидалось 2 записи для eth_usd, получено {len(eth_prices)}"

    for price in btc_prices:
        assert price.ticker == "btc_usd", "Некорректный тикер в записях btc_usd."

    for price in eth_prices:
        assert price.ticker == "eth_usd", "Некорректный тикер в записях eth_usd."
