"""
Модуль для инициализации Telegram клиента
"""
import logging
from telethon import TelegramClient
from config import API_ID, API_HASH, SESSION_PATH

logger = logging.getLogger(__name__)


def create_client():
    """
    Создает и возвращает Telegram клиент
    """
    try:
        if not API_ID or not API_HASH:
            raise ValueError("Не найдены переменные окружения API_ID или API_HASH.")
        
        api_id = int(API_ID)
        client = TelegramClient(SESSION_PATH, api_id, API_HASH)
        return client
    except (ValueError, TypeError) as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        logger.error("➡️ Пожалуйста, убедитесь, что API_ID является числом, и обе переменные установлены.")
        raise


async def initialize_client(client):
    """
    Инициализирует клиент и проверяет авторизацию
    """
    async with client:
        if not await client.is_user_authorized():
            logger.error("❌ Авторизация не удалась.")
            return False

        me = await client.get_me()
        user_info = f"{me.first_name or ''} (@{me.username})" if me else "Unknown User"
        logger.info(f"✅ Успешная авторизация под аккаунтом: {user_info.strip()}")
        return True
