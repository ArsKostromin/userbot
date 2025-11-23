import asyncio
import logging
from.telegram_client import create_client, initialize_client, set_client_instance
from.gifts_listener import register_gift_listener, process_chat_history
from api.server import set_client_instance as set_api_client_instance

logger = logging.getLogger(__name__)

async def main_userbot():
    client = create_client()

    try:
        if not await initialize_client(client):
            logger.error("❌ Не удалось инициализировать клиент")
            return

        # Устанавливаем клиент для использования в API
        set_client_instance(client)
        set_api_client_instance(client)
        logger.info("✅ Клиент установлен для API")

        # Регистрируем слушатель новых подарков (real-time)
        register_gift_listener(client)
        logger.info("✅ Слушатель новых подарков зарегистрирован")

        # Обрабатываем непрочитанные подарки из истории
        await process_chat_history(client)
        logger.info("✅ Обработка истории завершена")

        # Запускаем клиент в режиме ожидания новых сообщений
        logger.info("🔄 Userbot запущен и ожидает новые подарки...")
        await client.run_until_disconnected()

    except KeyboardInterrupt:
        logger.info("⏹️ Получен сигнал остановки")
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка: {e}")
    finally:
        await client.disconnect()
        logger.info("👋 Userbot остановлен")