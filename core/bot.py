import asyncio
import logging
from telegram_client import create_client, initialize_client
from gifts_listener import register_gift_listener, process_chat_history

logger = logging.getLogger(__name__)

async def main_userbot():
    """Основная логика userbot: слушает Telegram, ловит подарки и т.д."""
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
        logger.exception(f"❌ Критическая ошибка: {e}")
    finally:
        await client.disconnect()
        logger.info("👋 Userbot остановлен")
