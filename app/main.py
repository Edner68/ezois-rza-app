"""Главный файл FastAPI приложения РЗА.

Реализует пункты ТЗ:
- 4.1.1 Модуль "Объекты / ПС и РУ"
- 4.1.2 Модуль "Шкафы РЗА и устройства"
- 4.1.2 Модуль "Конфигурации и уставки"
- 4.2.x Подсистемы управления и отчётности
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import Base, engine
from .api import routers_objects

# Создание таблиц БД
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Приложение РЗА",
    description="Система автоматизации разработки и сопровождения шкафов РЗА по ГОСТ 34.602",
    version="0.1.0"
)

# CORS для разработки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(routers_objects.router)

@app.get("/")
def root():
    """Корневой эндпоинт с информацией о приложении."""
    return {
        "message": "Приложение РЗА для ЭЗОИС-СПб",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    """Проверка работоспособности приложения."""
    return {"status": "ok"}
