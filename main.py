import asyncio
import logging
import uvicorn
from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from api.server import app
from core.bot import main_userbot

# Настройка логов
logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL), datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)


# Используем события startup/shutdown для управления userbot
# Это позволяет запускать userbot в том же event loop, что и FastAPI
@app.on_event("startup")
async def startup_event():
    """Запускаем userbot при старте FastAPI"""
    userbot_task = asyncio.create_task(main_userbot())
    logger.info("🚀 Userbot запущен в фоновой задаче")
    # Сохраняем задачу в app.state для доступа при shutdown
    app.state.userbot_task = userbot_task


@app.on_event("shutdown")
async def shutdown_event():
    """Останавливаем userbot при остановке FastAPI"""
    if hasattr(app.state, 'userbot_task'):
        logger.info("⏹️ Остановка userbot...")
        app.state.userbot_task.cancel()
        try:
            await app.state.userbot_task
        except asyncio.CancelledError:
            logger.info("✅ Userbot остановлен")


if __name__ == "__main__":
    # Запускаем FastAPI с uvicorn в асинхронном режиме
    # Это использует один event loop для FastAPI и userbot
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        loop="asyncio"  # Используем asyncio event loop
    )

