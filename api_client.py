"""
Модуль для работы с Django API
Отправляет данные о подарках на сервер Django
"""
import aiohttp
import json
import logging
from config import API_BASE_URL, API_TOKEN, USER_ID

logger = logging.getLogger(__name__)


async def send_gift_to_api(gift_data: dict) -> bool:
    """
    Отправляет данные о подарке в Django API
    Поддерживает разные типы подарков: Star Gifts и обычные подарки пользователей
    """
    if not API_TOKEN:
        logger.warning("⚠️ API_TOKEN не установлен, пропускаем отправку в API")
        return False
    
    if not USER_ID:
        logger.warning("⚠️ USER_ID не установлен, пропускаем отправку в API")
        return False
    
    # Определяем тип подарка
    gift_type = gift_data.get("gift_type", "star_gift")
    logger.info(f"📤 Отправляю {gift_type} в Django API...")
    
    # Добавляем user_id к данным подарка
    gift_data_with_user = gift_data.copy()
    gift_data_with_user["user"] = int(USER_ID)
    
    # Логируем данные, которые отправляем
    logger.info("--- 📤 Данные для отправки в API ---")
    logger.info(f"   🎁 Тип подарка: {gift_type}")
    logger.info(f"   👤 Пользователь: {USER_ID}")
    logger.info(f"   🌐 URL: {API_BASE_URL}/api/gifts/adds-gift/")
    logger.info("--- 📤 JSON данные ---")
    print(json.dumps(gift_data_with_user, indent=2, ensure_ascii=False))
    logger.info("--- 📤 Конец данных ---")
    
    url = f"{API_BASE_URL}/api/gifts/adds-gift/"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            logger.info("🌐 Отправляю HTTP POST запрос...")
            async with session.post(url, json=gift_data_with_user, headers=headers) as response:
                response_text = await response.text()
                logger.info(f"📥 Получен ответ от API: {response.status}")
                logger.info(f"📥 Тело ответа: {response_text}")
                
                if response.status == 201:
                    logger.info(f"✅ {gift_type} успешно добавлен пользователю {USER_ID}")
                    return True
                else:
                    logger.error(f"❌ Ошибка API: {response.status} - {response_text}")
                    return False
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке в API: {e}")
        return False
