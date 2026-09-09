from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from ..config.config import settings

URL_DATABASE = settings.database_url

engine = create_async_engine(URL_DATABASE)

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    async with SessionLocal() as db:
        yield db