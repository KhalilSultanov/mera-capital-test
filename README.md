# Deribit Crypto Price API Service

## Overview

This project provides a FastAPI-based service to collect and serve cryptocurrency prices from Deribit. It periodically
fetches BTC/USD and ETH/USD prices and stores them in a SQLite database. The service also offers REST endpoints for
retrieving price data and filtered queries.

## Features

- Collects BTC/USD and ETH/USD prices every minute from the Deribit API.
- Stores price data in a SQLite database.
- Provides RESTful API endpoints to retrieve prices.
- Includes a Docker setup for easy deployment.
- GitHub Actions workflow for automatic testing.

## Technologies Used

- **Python**: 3.12
- **FastAPI**: Web framework for creating REST APIs.
- **SQLite**: Simple database for data storage.
- **Docker**: For containerizing the application.
- **GitHub Actions**: For continuous integration and running tests.

## Installation

### Prerequisites

- Docker
- Python 3.12

### Clone Repository

```sh
$ git clone https://github.com/KhalilSultanov/mera-capital-test.git
$ cd mera-capital-test
```

### Local Installation

1. **Create a virtual environment** and activate it:
   ```sh
   $ python -m venv venv
   $ source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. **Install dependencies**:
   ```sh
   $ pip install --upgrade pip
   $ pip install -r requirements.txt
   ```

3. **Set environment variables**:
   Create a `.env` file in the root directory with the following content:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///app/data/crypto_prices.db
   FETCH_INTERVAL=60
   API_HOST=0.0.0.0
   API_PORT=8000
   ```

4. **Run the application**:
   ```sh
   $ uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Running with Docker

1. **Build and run the Docker container**:
   ```sh
   $ docker-compose up --build
   ```

2. The application will be available at [http://localhost:8000](http://localhost:8000).

## API Endpoints

- `GET /prices?ticker=<ticker>`: Retrieve all price records for a specific ticker (e.g., `btc_usd` or `eth_usd`).
    - **Parameters**:
        - `ticker` (required): The ticker symbol for the cryptocurrency (e.g., `btc_usd`).
    - **Response**: Returns a list of all price records for the specified ticker.
    - **Response Codes**:
        - `200 OK`: Successfully retrieved the price records.
        - `404 Not Found`: No data found for the specified ticker.

- `GET /latest_price?ticker=<ticker>`: Retrieve the latest price record for a specific ticker.
    - **Parameters**:
        - `ticker` (required): The ticker symbol for the cryptocurrency (e.g., `btc_usd`).
    - **Response**: Returns the latest price record for the specified ticker.
    - **Response Codes**:
        - `200 OK`: Successfully retrieved the latest price record.
        - `404 Not Found`: No data found for the specified ticker.

- `GET /filtered_prices?ticker=<ticker>&start=<start>&end=<end>`: Retrieve price records for a specific ticker within a
  time range.
    - **Parameters**:
        - `ticker` (required): The ticker symbol for the cryptocurrency (e.g., `btc_usd`).
        - `start` (optional): The starting timestamp for filtering the price records.
        - `end` (optional): The ending timestamp for filtering the price records.
    - **Response**: Returns a list of price records for the specified ticker within the given time range.
    - **Response Codes**:
        - `200 OK`: Successfully retrieved the filtered price records.
        - `404 Not Found`: No data found for the specified ticker and/or timeframe.

## Running Tests

This project includes a comprehensive test suite using `pytest`.

### Running Tests Locally

1. **Activate the virtual environment**:
   ```sh
   $ source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

2. **Run the tests**:
   ```sh
   $ pytest
   ```

### Running Tests with GitHub Actions

The project is set up with a GitHub Actions workflow to automatically run tests on every push or pull request to
the `main` branch.

## Contact

For any questions or issues, please contact [Khalil Sultanov](https://github.com/KhalilSultanov).
