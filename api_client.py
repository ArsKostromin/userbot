"""
Модуль для работы с Django API
Отправляет данные о подарках на сервер Django
"""
import aiohttp
import logging
from config import API_BASE_URL, API_TOKEN, USER_ID

logger = logging.getLogger(__name__)


async def send_gift_to_api(gift_data: dict) -> bool:
    """
    Отправляет данные о подарке в Django API
    """
    if not API_TOKEN:
        logger.warning("⚠️ API_TOKEN не установлен, пропускаем отправку в API")
        return False
    
    if not USER_ID:
        logger.warning("⚠️ USER_ID не установлен, пропускаем отправку в API")
        return False
    
    # Добавляем user_id к данным подарка
    gift_data_with_user = gift_data.copy()
    gift_data_with_user["user"] = int(USER_ID)
    
    url = f"{API_BASE_URL}/api/gifts/adds-gift/"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=gift_data_with_user, headers=headers) as response:
                if response.status == 201:
                    logger.info(f"✅ Подарок успешно добавлен пользователю {USER_ID}")
                    return True
                else:
                    logger.error(f"❌ Ошибка API: {response.status} - {await response.text()}")
                    return False
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке в API: {e}")
        return False
