"""
Модуль для обработки авторизации Telegram
Содержит функции для автоматической авторизации с кодом из SMS
"""
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError
from config import PHONE_NUMBER, LOGIN_CODE

logger = logging.getLogger(__name__)


async def authorize_with_code(client: TelegramClient) -> bool:
    """
    Авторизует клиент с кодом из переменных окружения
    
    Args:
        client: Telegram клиент
        
    Returns:
        bool: True если авторизация успешна, False если нет
    """
    # Проверяем наличие номера телефона
    if not PHONE_NUMBER:
        logger.error("❌ PHONE_NUMBER не установлен в переменных окружения")
        return False
    
    try:
        # Отправляем код на номер телефона
        logger.info(f"📱 Отправляю код авторизации на номер: {PHONE_NUMBER}")
        await client.send_code_request(PHONE_NUMBER)
        
        # Проверяем наличие кода в переменных окружения
        if not LOGIN_CODE:
            logger.error("❌ LOGIN_CODE не установлен в переменных окружения")
            logger.error("💡 Получите код из SMS и установите переменную LOGIN_CODE")
            return False
        
        # Авторизуемся с кодом
        logger.info("🔑 Авторизуюсь с кодом из переменных окружения...")
        await client.sign_in(PHONE_NUMBER, LOGIN_CODE)
        
        logger.info("✅ Авторизация успешна!")
        return True
        
    except PhoneCodeInvalidError:
        logger.error("❌ Неверный код авторизации")
        logger.error("💡 Проверьте правильность кода в переменной LOGIN_CODE")
        return False
    except PhoneCodeExpiredError:
        logger.error("❌ Код авторизации истек")
        logger.error("💡 Получите новый код и обновите переменную LOGIN_CODE")
        return False
    except SessionPasswordNeededError:
        logger.error("❌ Требуется двухфакторная аутентификация")
        logger.error("💡 Отключите 2FA в настройках Telegram или добавьте поддержку пароля")
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка при авторизации: {e}")
        return False


async def check_authorization_status(client: TelegramClient) -> bool:
    """
    Проверяет статус авторизации клиента
    
    Args:
        client: Telegram клиент
        
    Returns:
        bool: True если пользователь авторизован, False если нет
    """
    try:
        return await client.is_user_authorized()
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке авторизации: {e}")
        return False
