import asyncpg
from app.config import settings

pool: asyncpg.Pool | None = None


async def connect(database_url: str):
    global pool
    url = database_url.replace("+asyncpg", "")
    if settings.db_pool_min_size > settings.db_pool_max_size:
        raise ValueError("DB_POOL_MIN_SIZE cannot be greater than DB_POOL_MAX_SIZE")

    pool = await asyncpg.create_pool(
        url,
        min_size=settings.db_pool_min_size,
        max_size=settings.db_pool_max_size,
    )


async def close():
    global pool
    if pool:
        await pool.close()


def get_pool() -> asyncpg.Pool:
    return pool
