# app/main.py
import logging
import sys

from fastapi import FastAPI

from app.api.router import router
from app.search.engine import SearchEngine
from app.data import db
from app.data.loader import load_all
from app.config import settings

app_logger = logging.getLogger("app")

if not app_logger.handlers:
    app_logger.setLevel(logging.INFO)
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(logging.Formatter("%(levelname)s: %(name)s: %(message)s"))
    app_logger.addHandler(h)

logger = logging.getLogger(__name__)
app = FastAPI(title="Product Search API")


@app.on_event("startup")
async def startup():
    await db.connect(settings.database_url)
    logger.info("DB connected")

    index = await load_all(db.get_pool())

    engine = SearchEngine(index)
    engine.load_model()

    app.state.engine = engine
    logger.info("Search engine ready")


@app.on_event("shutdown")
async def shutdown():
    await db.close()


app.include_router(router)
