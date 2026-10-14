from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.prices import router as prices_router
from app.database import create_engine
from app.models.price import Base
from app.api.dependencies import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    init_db(engine)
    yield
    await engine.dispose()


app = FastAPI(title="Deribit Price Service", lifespan=lifespan)
app.include_router(prices_router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok"}