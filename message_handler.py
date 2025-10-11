"""
Модуль для обработки сообщений Telegram
Логирует ВСЕ сообщения и обрабатывает Star Gifts

Логика обработки сообщений находится в файле: message_handler.py
"""
import json
import logging
from gift_processor import extract_gift_data, get_sender_info
from api_client import send_gift_to_api

logger = logging.getLogger(__name__)


async def handle_new_message(event, client):
    """
    Обрабатывает ВСЕ новые сообщения и логирует их
    Проверяет, является ли сообщение Star Gift и обрабатывает соответственно
    
    Логика находится в файле: message_handler.py
    """
    message = event.message
    
    # Получаем информацию о чате для логирования
    try:
        chat = await client.get_entity(message.chat_id)
        chat_name = getattr(chat, 'title', getattr(chat, 'username', f"Chat {message.chat_id}"))
        chat_username = getattr(chat, 'username', None)
    except Exception as e:
        chat_name = f"Unknown Chat {message.chat_id}"
        chat_username = None
        logger.debug(f"Не удалось получить информацию о чате {message.chat_id}: {e}")
    
    # Получаем информацию об отправителе
    sender_id = getattr(message, 'sender_id', None)
    sender_info = None
    if sender_id:
        try:
            sender_info = await get_sender_info(client, sender_id)
        except Exception as e:
            logger.debug(f"Не удалось получить информацию об отправителе {sender_id}: {e}")
    
    # Формируем информацию об отправителе для логов
    sender_name = "Unknown"
    sender_username = ""
    if sender_info:
        sender_name = sender_info.get('sender_first_name', 'Unknown')
        sender_username = sender_info.get('sender_username', '')
        if sender_username:
            sender_display = f"{sender_name} (@{sender_username})"
        else:
            sender_display = sender_name
    else:
        sender_display = f"User {sender_id}" if sender_id else "Unknown"
    
    # Логируем ВСЕ сообщения
    logger.info(f"📨 Новое сообщение в чате '{chat_name}' от {sender_display}")
    logger.info(f"   📍 Чат ID: {message.chat_id}")
    logger.info(f"   📍 Сообщение ID: {getattr(message, 'id', 'N/A')}")
    logger.info(f"   📍 Дата: {getattr(message, 'date', 'N/A')}")
    
    # Логируем тип сообщения
    message_type = "Текстовое сообщение"
    if getattr(message, 'action', None):
        action_type = type(message.action).__name__
        message_type = f"Действие: {action_type}"
        logger.info(f"   🎭 Тип: {message_type}")
        
        # Обрабатываем разные типы подарков
        if action_type == 'MessageActionStarGiftUnique':
            logger.warning(f"🎁 НАЙДЕН STAR GIFT в чате '{chat_name}'!")
            await handle_star_gift(message, client, chat_name, chat_username, sender_info)
        elif action_type == 'MessageActionUserGift':
            logger.warning(f"🎁 НАЙДЕН ОБЫЧНЫЙ ПОДАРОК в чате '{chat_name}'!")
            await handle_user_gift(message, client, chat_name, chat_username, sender_info)
    else:
        # Логируем содержимое текстового сообщения (если есть)
        text_content = getattr(message, 'text', '')
        if text_content:
            # Ограничиваем длину текста для логов
            display_text = text_content[:100] + "..." if len(text_content) > 100 else text_content
            logger.info(f"   📝 Текст: {display_text}")
        else:
            logger.info(f"   📝 Тип: {message_type}")
    
    # Логируем медиа (если есть)
    if hasattr(message, 'media') and message.media:
        logger.info(f"   🖼️ Медиа: {type(message.media).__name__}")
    
    logger.info("   " + "─" * 50)  # Разделитель для читаемости логов


async def handle_star_gift(message, client, chat_name, chat_username, sender_info):
    """
    Обрабатывает Star Gift сообщение
    Выделено в отдельную функцию для лучшей читаемости
    """
    # Извлекаем данные о подарке
    gift_data = extract_gift_data(message.action, message)
    
    # Добавляем информацию о чате в данные подарка
    gift_data["chat_info"] = {
        "chat_id": message.chat_id,
        "chat_name": chat_name,
        "chat_username": chat_username
    }
    
    # Добавляем информацию об отправителе
    if sender_info:
        gift_data["sender_info"] = sender_info
        
        # Логируем информацию об отправителе
        sender_name = sender_info.get('sender_first_name', 'Unknown')
        sender_username = sender_info.get('sender_username', '')
        if sender_username:
            logger.info(f"👤 Отправитель подарка: {sender_name} (@{sender_username})")
        else:
            logger.info(f"👤 Отправитель подарка: {sender_name}")
    
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


async def handle_user_gift(message, client, chat_name, chat_username, sender_info):
    """
    Обрабатывает обычный подарок пользователя (MessageActionUserGift)
    """
    logger.info("🔍 Анализирую обычный подарок пользователя...")
    
    # Логируем всю информацию о подарке
    action = message.action
    logger.info("--- 📋 Полная информация о подарке ---")
    logger.info(f"   🎁 Тип действия: {type(action).__name__}")
    
    # Извлекаем доступную информацию из action
    gift_data = {
        "gift_type": "user_gift",
        "message_id": getattr(message, 'id', None),
        "chat_id": message.chat_id,
        "chat_name": chat_name,
        "chat_username": chat_username,
        "date": str(getattr(message, 'date', 'N/A')),
    }
    
    # Добавляем информацию об отправителе
    if sender_info:
        gift_data["sender_info"] = sender_info
        sender_name = sender_info.get('sender_first_name', 'Unknown')
        sender_username = sender_info.get('sender_username', '')
        if sender_username:
            logger.info(f"👤 Отправитель подарка: {sender_name} (@{sender_username})")
        else:
            logger.info(f"👤 Отправитель подарка: {sender_name}")
    
    # Пытаемся извлечь дополнительную информацию из action
    try:
        # Логируем все доступные атрибуты action
        logger.info("   🔍 Доступные атрибуты action:")
        for attr_name in dir(action):
            if not attr_name.startswith('_'):
                try:
                    attr_value = getattr(action, attr_name)
                    if not callable(attr_value):
                        logger.info(f"      {attr_name}: {attr_value}")
                        gift_data[f"action_{attr_name}"] = str(attr_value)
                except Exception as e:
                    logger.debug(f"      {attr_name}: <не удалось получить: {e}>")
        
        # Пытаемся найти информацию о подарке
        if hasattr(action, 'gift'):
            gift_info = action.gift
            logger.info("   🎁 Найдена информация о подарке:")
            gift_data["gift_info"] = {}
            
            for attr_name in dir(gift_info):
                if not attr_name.startswith('_'):
                    try:
                        attr_value = getattr(gift_info, attr_name)
                        if not callable(attr_value):
                            logger.info(f"      gift.{attr_name}: {attr_value}")
                            gift_data["gift_info"][attr_name] = str(attr_value)
                    except Exception as e:
                        logger.debug(f"      gift.{attr_name}: <не удалось получить: {e}>")
        
        # Пытаемся найти информацию о получателе
        if hasattr(action, 'user_id'):
            recipient_id = action.user_id
            logger.info(f"   👤 Получатель подарка: {recipient_id}")
            gift_data["recipient_id"] = recipient_id
            
            # Пытаемся получить информацию о получателе
            try:
                recipient_info = await get_sender_info(client, recipient_id)
                gift_data["recipient_info"] = recipient_info
                recipient_name = recipient_info.get('sender_first_name', 'Unknown')
                recipient_username = recipient_info.get('sender_username', '')
                if recipient_username:
                    logger.info(f"   👤 Получатель: {recipient_name} (@{recipient_username})")
                else:
                    logger.info(f"   👤 Получатель: {recipient_name}")
            except Exception as e:
                logger.warning(f"   ⚠️ Не удалось получить информацию о получателе: {e}")
        
    except Exception as e:
        logger.error(f"   ❌ Ошибка при анализе подарка: {e}")
    
    # Выводим полные данные в консоль
    logger.info("--- 📦 Полные данные о подарке (JSON-формат) ---")
    print(json.dumps(gift_data, indent=4, ensure_ascii=False))
    logger.info("--------------------------------------------------")
    
    # Отправляем данные в API
    logger.info("🚀 Отправляю данные о подарке в Django API...")
    api_success = await send_gift_to_api(gift_data)
    if api_success:
        logger.info("🎉 Обычный подарок успешно обработан и сохранен!")
    else:
        logger.warning("⚠️ Обычный подарок найден, но не удалось сохранить в API")