"""
Модуль для инициализации Telegram клиента
Создает и настраивает подключение к Telegram API
"""
import logging
from telethon import TelegramClient
from config import API_ID, API_HASH, SESSION_PATH
from auth_handler import authorize_with_code, check_authorization_status

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
    Если сессии нет, пытается авторизоваться автоматически
    """
    # Подключаемся к клиенту
    await client.connect()
    
    # Проверяем статус авторизации
    if not await check_authorization_status(client):
        logger.info("🔐 Сессия не найдена, начинаю процесс авторизации...")
        
        # Пытаемся авторизоваться с кодом
        if not await authorize_with_code(client):
            await client.disconnect()
            return False

    # Получаем информацию о текущем пользователе
    me = await client.get_me()
    user_info = f"{me.first_name or ''} (@{me.username})" if me else "Unknown User"
    logger.info(f"✅ Успешная авторизация под аккаунтом: {user_info.strip()}")
    return True
