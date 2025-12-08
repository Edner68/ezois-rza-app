"""Конфигурация приложения РЗА."""

from functools import lru_cache
from typing import List

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Настройки FastAPI сервиса."""

    project_name: str = "Приложение РЗА"
    description: str = (
        "Система автоматизации разработки и сопровождения шкафов РЗА по ГОСТ 34.602"
    )
    version: str = "0.1.0"
    database_url: str = Field(
        default="sqlite+aiosqlite:///./rza.db",
        description="Строка подключения к БД SQLite через SQLAlchemy.",
    )
    debug_sql: bool = Field(
        default=False, description="Включает вывод SQL-запросов для отладки."
    )
    audit_enabled: bool = Field(
        default=True, description="Флаг включения аудита критичных операций."
    )
    default_actor: str = Field(
        default="system", description="Идентификатор исполнителя по умолчанию."
    )
    allowed_origins: List[str] = Field(
        default_factory=lambda: ["*"], description="Список разрешённых источников CORS."
    )
    docs_url: str = Field(default="/docs", description="Путь к Swagger UI.")
    redoc_url: str = Field(default="/redoc", description="Путь к ReDoc.")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Возвращает кэшированный экземпляр настроек."""

    return Settings()


settings = get_settings()
