from fastapi import FastAPI
from app.database import Database
from app.services import PriceFetcher
from app.routers import prices
from app.config import settings
from contextlib import asynccontextmanager
from fastapi import Request


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = Database()
    await db.initialize()

    price_fetcher = PriceFetcher(db=db)
    await price_fetcher.start()

    app.state.database = db

    try:
        yield
    finally:
        await price_fetcher.shutdown()


app = FastAPI(lifespan=lifespan)

app.include_router(prices.router)


async def get_db(request: Request) -> Database:
    return request.app.state.database


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.api_host, port=settings.api_port, reload=True)
