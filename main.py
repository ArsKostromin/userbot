import asyncio
import logging
import threading
import uvicorn
from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from api.server import app
from core.bot import main_userbot

# Настройка логов
logging.basicConfig(format=LOG_FORMAT, level=getattr(logging, LOG_LEVEL), datefmt=LOG_DATE_FORMAT)
logger = logging.getLogger(__name__)

def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")

if __name__ == "__main__":
    # Запуск FastAPI и userbot параллельно
    server_thread = threading.Thread(target=run_fastapi, daemon=True)
    server_thread.start()

    asyncio.run(main_userbot())

