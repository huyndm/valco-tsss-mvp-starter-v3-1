from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="ValCo TSSS MVP V3.1", version="0.2.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "app": "ValCo TSSS MVP V3.1"}


app.include_router(router, prefix="/api/v1")
