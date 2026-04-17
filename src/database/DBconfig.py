import os
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.database.DBmodels import *


load_dotenv()
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB = os.getenv("POSTGRES_DB")
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@postgres:5432/{POSTGRES_DB}"


engine = create_async_engine(
    DATABASE_URL,
    pool_size=5, 
    max_overflow=10,
    pool_pre_ping=True,
)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()