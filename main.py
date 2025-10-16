import asyncio
import logging
import threading
import uvicorn
from fastapi import FastAPI, Request

# Твои импорты
from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from telegram_client import create_client, initialize_client
from gifts_listener import register_gift_listener, process_chat_history

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL),
    datefmt=LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)

app = FastAPI()


@app.post("/test")
async def test_endpoint(request: Request):
    data = await request.json()
    logger.info(f"📩 Получен запрос от Django: {data}")
    return {"status": "ok", "message": "Запрос дошёл до userbot!"}


async def main_userbot():
    """
    Основная логика userbot'а: слушает Telegram, ловит подарки и т.д.
    """
    client = create_client()

    try:
        if not await initialize_client(client):
            logger.error("❌ Не удалось инициализировать клиент")
            return

        await process_chat_history(client)
        register_gift_listener(client)

        logger.info("🔄 Userbot запущен и мониторит чаты в реальном времени...")

        await client.run_until_disconnected()

    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await client.disconnect()
        logger.info("👋 Userbot остановлен")


def run_fastapi():
    """Запускает FastAPI сервер в отдельном потоке"""
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")


if __name__ == "__main__":
    # Запускаем FastAPI и userbot параллельно
    server_thread = threading.Thread(target=run_fastapi, daemon=True)
    server_thread.start()

    asyncio.run(main_userbot())
