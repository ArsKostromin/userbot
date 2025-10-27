import asyncio
import logging
from .telegram_client import create_client, initialize_client
from .sender import send_snakebox_gift

logger = logging.getLogger(__name__)

async def main_userbot():
    client = create_client()

    try:
        if not await initialize_client(client):
            logger.error("❌ Не удалось инициализировать клиент")
            return

        # 👇 тут единственное действие — отправка подарка
        await send_snakebox_gift(client)

        logger.info("🎉 Отправка завершена, бота можно останавливать.")
        await asyncio.sleep(2)

    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")
    finally:
        await client.disconnect()
        logger.info("👋 Userbot остановлен")
