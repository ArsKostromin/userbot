import asyncio
import logging
import threading
import uvicorn

from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from api.server import app
from core.bot import main_userbot
from TDLib.main import run_tdlib  # 👈 добавили TDLib

# --- ЛОГИ ---
logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL), datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)


def run_fastapi():
    """Запускаем FastAPI в отдельном потоке"""
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")


def start_fastapi_thread():
    """Создаём поток для FastAPI"""
    server_thread = threading.Thread(target=run_fastapi, daemon=True)
    server_thread.start()
    logger.info("⚙️ FastAPI сервер запущен на :8080")


async def start_all():
    """Параллельный запуск Telethon userbot и TDLib"""
    start_fastapi_thread()

    # запускаем оба клиента в отдельных async задачах
    userbot_task = asyncio.create_task(main_userbot())
    tdlib_task = asyncio.create_task(run_tdlib())

    logger.info("🚀 Запуск Userbot (Telethon) и TDLib клиента...")
    await asyncio.gather(userbot_task, tdlib_task)


if __name__ == "__main__":
    try:
        asyncio.run(start_all())
    except KeyboardInterrupt:
        logger.info("🛑 Завершение всех процессов пользователем...")
