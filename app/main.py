"""Главный файл FastAPI приложения РЗА.

Реализует пункты ТЗ:
- 4.1.1 Модуль "Объекты / ПС и РУ"
- 4.1.2 Модуль "Шкафы РЗА и устройства"
- 4.1.2 Модуль "Конфигурации и уставки"
- 4.2.x Подсистемы управления и отчётности
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import routers_configs, routers_objects, routers_panels, routers_reports
from .config import settings
from .db import init_db

app = FastAPI(
    title=settings.project_name,
    description=settings.description,
    version=settings.version,
)

# CORS для разработки и тестирования
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup() -> None:
    """Создаёт структуру БД при запуске."""
    await init_db()


# Подключение роутеров
app.include_router(routers_objects.router)
app.include_router(routers_panels.router)
app.include_router(routers_configs.router)
app.include_router(routers_reports.router)


@app.get("/")
async def root() -> dict:
    """Корневой эндпоинт с информацией о приложении."""
    return {
        "message": settings.project_name,
        "version": settings.version,
        "docs": settings.docs_url if hasattr(settings, "docs_url") else "/docs",
        "redoc": settings.redoc_url if hasattr(settings, "redoc_url") else "/redoc",
    }


@app.get("/health")
async def health_check() -> dict:
    """Проверка работоспособности приложения."""
    return {"status": "ok"}
