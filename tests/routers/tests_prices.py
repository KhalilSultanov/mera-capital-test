import pytest
from app.models import PriceResponse


@pytest.mark.asyncio
async def test_get_all_prices_missing_ticker(client, mock_db):
    """
    Тестирует, что эндпоинт /prices возвращает 422 при отсутствии параметра 'ticker'.
    """
    response = await client.get("/prices")  # Не передаём 'ticker'

    assert response.status_code == 422, f"Expected status 422, got {response.status_code}"
    data = response.json()
    assert "detail" in data, "Expected 'detail' in response"
    # Проверка, что ошибка связана с полем 'ticker'
    assert any(error['loc'][-1] == 'ticker' for error in data['detail']), "Expected error in 'ticker' field."


@pytest.mark.asyncio
async def test_get_filtered_prices_invalid_start_type(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices возвращает 422 при некорректном типе параметра 'start'.
    """
    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "start": "invalid_start",
        "end": 1625079000
    })

    assert response.status_code == 422, f"Expected status 422, got {response.status_code}"
    data = response.json()
    assert "detail" in data, "Expected 'detail' in response"
    assert any(error['loc'][-1] == 'start' for error in data['detail']), "Expected error in 'start' field."


@pytest.mark.asyncio
async def test_get_filtered_prices_invalid_end_type(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices возвращает 422 при некорректном типе параметра 'end'.
    """
    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "start": 1625078000,
        "end": "invalid_end"
    })

    assert response.status_code == 422, f"Expected status 422, got {response.status_code}"
    data = response.json()
    assert "detail" in data, "Expected 'detail' in response"
    assert any(error['loc'][-1] == 'end' for error in data['detail']), "Expected error in 'end' field."


@pytest.mark.asyncio
async def test_get_filtered_prices_start_greater_than_end(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает случай, когда 'start' > 'end'.
    """
    # Настраиваем мок для возврата пустого списка
    mock_db.get_filtered_prices.return_value = []

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "start": 1625079000,  # start > end
        "end": 1625078000
    })

    assert response.status_code == 404, f"Expected status 404, got {response.status_code}"
    data = response.json()
    assert data["detail"] == "No data found for the specified ticker and/or timeframe"


@pytest.mark.asyncio
async def test_get_filtered_prices_only_start(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает случай, когда указан только параметр 'start'.
    """
    # Настраиваем мок для возврата списка цен начиная с 'start'
    filtered_prices = [
        PriceResponse(ticker="btc_usd", price=50500.0, timestamp=1625078400),
        PriceResponse(ticker="btc_usd", price=51000.0, timestamp=1625079000)
    ]
    mock_db.get_filtered_prices.return_value = filtered_prices

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "start": 1625078000
        # 'end' не указан
    })

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 2, f"Expected 2 filtered prices, got {len(data)}"
    assert data[0]["price"] == 50500.0
    assert data[0]["timestamp"] == 1625078400
    assert data[1]["price"] == 51000.0
    assert data[1]["timestamp"] == 1625079000


@pytest.mark.asyncio
async def test_get_filtered_prices_only_end(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает случай, когда указан только параметр 'end'.
    """
    # Настраиваем мок для возврата списка цен до 'end'
    filtered_prices = [
        PriceResponse(ticker="btc_usd", price=50000.0, timestamp=1625077800),
        PriceResponse(ticker="btc_usd", price=50500.0, timestamp=1625078400)
    ]
    mock_db.get_filtered_prices.return_value = filtered_prices

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "end": 1625078500
        # 'start' не указан
    })

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 2, f"Expected 2 filtered prices, got {len(data)}"
    assert data[0]["price"] == 50000.0
    assert data[0]["timestamp"] == 1625077800
    assert data[1]["price"] == 50500.0
    assert data[1]["timestamp"] == 1625078400


@pytest.mark.asyncio
async def test_get_filtered_prices_start_equals_end(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает случай, когда 'start' == 'end'.
    """
    # Настраиваем мок для возврата одной цены, если такая существует
    filtered_prices = [
        PriceResponse(ticker="btc_usd", price=50500.0, timestamp=1625078400)
    ]
    mock_db.get_filtered_prices.return_value = filtered_prices

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "start": 1625078400,
        "end": 1625078400
    })

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 1, f"Expected 1 filtered price, got {len(data)}"
    assert data[0]["price"] == 50500.0
    assert data[0]["timestamp"] == 1625078400


@pytest.mark.asyncio
async def test_get_filtered_prices_invalid_combination(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает некорректные комбинации параметров.
    Например, 'start' как строка и 'end' как отрицательное число.
    """
    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "start": "invalid_start",  # Некорректный тип
        "end": -1625078000  # Отрицательное число (допустимо, если нет ограничений)
    })

    assert response.status_code == 422, f"Expected status 422, got {response.status_code}"
    data = response.json()
    assert "detail" in data, "Expected 'detail' in response"
    # Проверка, что ошибка связана с 'start'
    assert any(error['loc'][-1] == 'start' for error in data['detail']), "Expected error in 'start' field."
    # Удаляем проверку на поле 'end'
    # assert any(error['loc'][-1] == 'end' for error in data['detail']), "Expected error in 'end' field."


@pytest.mark.asyncio
async def test_get_filtered_prices_start_none_end_none(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает случай, когда 'start' и 'end' не указаны.
    Ожидается получение всех цен для тикера.
    """
    # Настраиваем мок для возврата всех цен
    mock_prices = [
        PriceResponse(ticker="btc_usd", price=50000.0, timestamp=1625077800),
        PriceResponse(ticker="btc_usd", price=50500.0, timestamp=1625078400),
        PriceResponse(ticker="btc_usd", price=51000.0, timestamp=1625079000)
    ]
    mock_db.get_filtered_prices.return_value = mock_prices

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd"
        # 'start' и 'end' не указаны
    })

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 3, f"Expected 3 filtered prices, got {len(data)}"
    assert data[0]["price"] == 50000.0
    assert data[0]["timestamp"] == 1625077800
    assert data[1]["price"] == 50500.0
    assert data[1]["timestamp"] == 1625078400
    assert data[2]["price"] == 51000.0
    assert data[2]["timestamp"] == 1625079000


@pytest.mark.asyncio
async def test_get_filtered_prices_invalid_parameter_combination(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает некорректные комбинации параметров.
    Например, 'start' отсутствует, но 'end' указан.
    """
    # Настраиваем мок для возврата списка цен до 'end'
    filtered_prices = [
        PriceResponse(ticker="btc_usd", price=50000.0, timestamp=1625077800),
        PriceResponse(ticker="btc_usd", price=50500.0, timestamp=1625078400)
    ]
    mock_db.get_filtered_prices.return_value = filtered_prices

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "end": 1625078400
        # 'start' не указан
    })

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 2, f"Expected 2 filtered prices, got {len(data)}"
    assert data[0]["price"] == 50000.0
    assert data[0]["timestamp"] == 1625077800
    assert data[1]["price"] == 50500.0
    assert data[1]["timestamp"] == 1625078400


@pytest.mark.asyncio
async def test_get_filtered_prices_large_dataset(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает большие объёмы данных.
    """
    # Создаём большой список цен
    large_filtered_prices = [
        PriceResponse(ticker="btc_usd", price=50000.0 + i, timestamp=1625077800 + i)
        for i in range(1000)  # 1000 записей
    ]
    mock_db.get_filtered_prices.return_value = large_filtered_prices

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "start": 1625077800,
        "end": 1625078800
    })

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 1000, f"Expected 1000 filtered prices, got {len(data)}"
    # Проверка первых и последних записей
    assert data[0]["price"] == 50000.0
    assert data[0]["timestamp"] == 1625077800
    assert data[-1]["price"] == 50999.0  # 50000 + 999
    assert data[-1]["timestamp"] == 1625078799  # 1625077800 + 999


@pytest.mark.asyncio
async def test_get_filtered_prices_start_negative_end_positive(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает случай, когда 'start' отрицательный, а 'end' положительный.
    Ожидается получение пустого списка.
    """
    # Настраиваем мок для возврата пустого списка
    mock_db.get_filtered_prices.return_value = []

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "start": -1000,
        "end": 1625078000
    })

    assert response.status_code == 404, f"Expected status 404, got {response.status_code}"
    data = response.json()
    assert data["detail"] == "No data found for the specified ticker and/or timeframe"


@pytest.mark.asyncio
async def test_get_filtered_prices_start_none_end_positive(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает случай, когда 'start' не указан, а 'end' указан.
    """
    # Настраиваем мок для возврата списка цен до 'end'
    filtered_prices = [
        PriceResponse(ticker="btc_usd", price=50000.0, timestamp=1625077800),
        PriceResponse(ticker="btc_usd", price=50500.0, timestamp=1625078400)
    ]
    mock_db.get_filtered_prices.return_value = filtered_prices

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "end": 1625078400
    })

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 2, f"Expected 2 filtered prices, got {len(data)}"
    assert data[0]["price"] == 50000.0
    assert data[0]["timestamp"] == 1625077800
    assert data[1]["price"] == 50500.0
    assert data[1]["timestamp"] == 1625078400


@pytest.mark.asyncio
async def test_get_filtered_prices_start_positive_end_none(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает случай, когда 'start' указан, а 'end' не указан.
    """
    # Настраиваем мок для возврата списка цен начиная с 'start'
    filtered_prices = [
        PriceResponse(ticker="btc_usd", price=50500.0, timestamp=1625078400),
        PriceResponse(ticker="btc_usd", price=51000.0, timestamp=1625079000)
    ]
    mock_db.get_filtered_prices.return_value = filtered_prices

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "start": 1625078400
    })

    assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
    data = response.json()
    assert isinstance(data, list), "Response should be a list"
    assert len(data) == 2, f"Expected 2 filtered prices, got {len(data)}"
    assert data[0]["price"] == 50500.0
    assert data[0]["timestamp"] == 1625078400
    assert data[1]["price"] == 51000.0
    assert data[1]["timestamp"] == 1625079000


@pytest.mark.asyncio
async def test_get_filtered_prices_zero_timestamps(client, mock_db):
    """
    Тестирует, что эндпоинт /filtered_prices корректно обрабатывает случай, когда 'start' и 'end' равны нулю.
    """
    # Настраиваем мок для возврата пустого списка
    mock_db.get_filtered_prices.return_value = []

    response = await client.get("/filtered_prices", params={
        "ticker": "btc_usd",
        "start": 0,
        "end": 0
    })

    assert response.status_code == 404, f"Expected status 404, got {response.status_code}"
    data = response.json()
    assert data["detail"] == "No data found for the specified ticker and/or timeframe"


@pytest.mark.asyncio
async def test_get_all_prices_empty_ticker(client, mock_db):
    """
    Тестирует, что эндпоинт /prices корректно обрабатывает случай, когда 'ticker' пустая строка.
    """
    response = await client.get("/prices", params={"ticker": ""})  # Пустая строка

    assert response.status_code == 404, f"Expected status 404, got {response.status_code}"
    data = response.json()
    assert data["detail"] == "No data found for the specified ticker"
