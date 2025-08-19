from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from notisense_api.domain.utilities.config import settings

# Ensure the database URL uses asyncpg
if not settings.DATABASE_URL.startswith("postgresql+asyncpg://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(settings.DATABASE_URL, echo=True, pool_pre_ping=True, pool_recycle=300, pool_timeout=30)
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession, autocommit=False, autoflush=False
)

Base = declarative_base()


async def get_db():
    async with async_session() as session:
        yield session
