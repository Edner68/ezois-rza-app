"""Модуль работы с базой данных SQLite через SQLAlchemy."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Базовый класс моделей SQLAlchemy."""


engine = create_async_engine(
    settings.database_url,
    echo=settings.debug_sql,
    future=True,
)
async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Провайдер сессий для зависимостей FastAPI."""

    async with async_session_factory() as session:
        yield session


async def init_db() -> None:
    """Инициализирует БД и создаёт таблицы."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
