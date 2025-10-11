"""
Модуль для обработки сообщений Telegram
"""
import json
import logging
from gift_processor import extract_gift_data, get_sender_info
from api_client import send_gift_to_api

logger = logging.getLogger(__name__)


async def handle_new_message(event, client):
    """
    Обрабатывает новое сообщение и проверяет, является ли оно Star Gift
    Теперь мониторит ВСЕ чаты, а не только один конкретный
    """
    message = event.message
    
    # Получаем информацию о чате для логирования
    try:
        chat = await client.get_entity(message.chat_id)
        chat_name = getattr(chat, 'title', getattr(chat, 'username', f"Chat {message.chat_id}"))
    except Exception as e:
        chat_name = f"Unknown Chat {message.chat_id}"
        logger.debug(f"Не удалось получить информацию о чате {message.chat_id}: {e}")
    
    # Проверяем, является ли сообщение Star Gift
    if getattr(message, 'action', None) and type(message.action).__name__ == 'MessageActionStarGiftUnique':
        logger.warning(f"🎁 Найден новый Star Gift в чате '{chat_name}' (MSG_ID: {getattr(message, 'id', 'N/A')})!")
        
        # Извлекаем данные о подарке
        gift_data = extract_gift_data(message.action, message)
        
        # Добавляем информацию о чате в данные подарка
        gift_data["chat_info"] = {
            "chat_id": message.chat_id,
            "chat_name": chat_name,
            "chat_username": getattr(chat, 'username', None) if 'chat' in locals() else None
        }
        
        # Получаем информацию об отправителе
        sender_id = getattr(message, 'sender_id', None)
        if sender_id:
            sender_info = await get_sender_info(client, sender_id)
            gift_data["sender_info"] = sender_info
            
            # Логируем информацию об отправителе
            sender_name = sender_info.get('sender_first_name', 'Unknown')
            sender_username = sender_info.get('sender_username', '')
            if sender_username:
                logger.info(f"👤 Отправитель: {sender_name} (@{sender_username})")
            else:
                logger.info(f"👤 Отправитель: {sender_name}")
        
        # Выводим данные в консоль
        logger.info("--- 📦 Данные для GiftSerializer (JSON-формат) ---")
        print(json.dumps(gift_data, indent=4, ensure_ascii=False))
        logger.info("--------------------------------------------------")
        
        # Отправляем данные в API
        api_success = await send_gift_to_api(gift_data)
        if api_success:
            logger.info("🎉 Подарок успешно обработан и сохранен!")
        else:
            logger.warning("⚠️ Подарок найден, но не удалось сохранить в API")
    else:
        # Логируем обычные сообщения для отладки (только если это не спам)
        logger.debug(f"📨 Обычное сообщение в чате '{chat_name}' от пользователя {getattr(message, 'sender_id', 'Unknown')}")
