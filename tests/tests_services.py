import pytest
from unittest.mock import AsyncMock, patch, ANY
from app.services import PriceFetcher
from app.database import Database
import asyncio


@pytest.mark.asyncio
async def test_fetch_price_success():
    """
    Тестирует успешное получение цены из внешнего API и возвращение корректного значения.
    """
    mock_db = AsyncMock(spec=Database)
    fetcher = PriceFetcher(db=mock_db)

    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {'result': {'index_price': 50000.0}}
        mock_get.return_value.__aenter__.return_value = mock_response

        price = await fetcher.fetch_price('http://fakeurl.com')

        assert price == 50000.0


@pytest.mark.asyncio
async def test_fetch_price_no_price():
    """
    Тестирует поведение метода fetch_price, когда ответ от API не содержит цены.
    Ожидается возвращение None.
    """
    mock_db = AsyncMock(spec=Database)
    fetcher = PriceFetcher(db=mock_db)

    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {'result': {}}
        mock_get.return_value.__aenter__.return_value = mock_response

        price = await fetcher.fetch_price('http://fakeurl.com')

        assert price is None


@pytest.mark.asyncio
async def test_fetch_price_exception():
    """
    Тестирует обработку исключений при выполнении HTTP-запроса в методе fetch_price.
    Ожидается возвращение None при возникновении исключения.
    """
    mock_db = AsyncMock(spec=Database)
    fetcher = PriceFetcher(db=mock_db)

    with patch('aiohttp.ClientSession.get', side_effect=Exception('Network error')) as mock_get:
        price = await fetcher.fetch_price('http://fakeurl.com')

        assert price is None


@pytest.mark.asyncio
async def test_fetch_prices_loop_success():
    """
    Тестирует успешный цикл получения цен из API и их сохранение в базу данных.
    Ожидается корректное сохранение полученных цен и вызов соответствующих методов базы данных.
    """
    mock_db = AsyncMock(spec=Database)
    fetcher = PriceFetcher(db=mock_db, interval=0.1)

    with patch.object(fetcher, 'fetch_price') as mock_fetch_price:
        mock_fetch_price.side_effect = [50000.0, 3000.0, asyncio.CancelledError()]

        with patch.object(mock_db, 'insert_price', new_callable=AsyncMock) as mock_insert_price:
            with pytest.raises(asyncio.CancelledError):
                await fetcher.fetch_prices_loop()

            assert mock_fetch_price.call_count == 3, f"Expected 3 calls, got {mock_fetch_price.call_count}"
            mock_insert_price.assert_any_await("btc_usd", 50000.0, ANY)
            mock_insert_price.assert_any_await("eth_usd", 3000.0, ANY)

    await fetcher.shutdown()


@pytest.mark.asyncio
async def test_fetch_prices_loop_partial_failure():
    """
    Тестирует цикл получения цен из API при частичном отсутствии данных.
    Ожидается, что метод insert_price не будет вызван, и будет зафиксовано предупреждение в логах.
    """
    mock_db = AsyncMock(spec=Database)
    fetcher = PriceFetcher(db=mock_db, interval=0.1)

    with patch.object(fetcher, 'fetch_price') as mock_fetch_price:
        mock_fetch_price.side_effect = [50000.0, None, asyncio.CancelledError()]

        with patch.object(mock_db, 'insert_price', new_callable=AsyncMock) as mock_insert_price:
            with patch('app.services.logger') as mock_logger:
                with pytest.raises(asyncio.CancelledError):
                    await fetcher.fetch_prices_loop()

                assert mock_fetch_price.call_count == 3, f"Expected 3 calls, got {mock_fetch_price.call_count}"
                mock_insert_price.assert_not_called()
                mock_logger.warning.assert_called_once_with("Failed to fetch one or both prices.")

    await fetcher.shutdown()
