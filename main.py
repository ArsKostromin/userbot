import asyncio
import logging

from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from telegram_client import create_client, initialize_client
from gifts_listener import register_gift_listener

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL),
    datefmt=LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


async def main():
    """
    Userbot, который мониторит ВСЕ новые сообщения на предмет Star Gifts, NFT и обычных подарков
    """
    client = create_client()

    try:
        if not await initialize_client(client):
            logger.error("❌ Не удалось инициализировать клиент")
            return

        # --- Подключаем listener для всех подарков ---
        register_gift_listener(client)

        logger.info("🔄 Userbot запущен. Мониторит все чаты на предмет NFT/Star Gifts...")
        logger.info("💡 Для остановки нажмите Ctrl+C")

        # --- Запускаем вечный цикл ---
        await client.run_until_disconnected()

    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await client.disconnect()
        logger.info("👋 Userbot остановлен")


if __name__ == "__main__":
    asyncio.run(main())
