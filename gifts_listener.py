from telethon import events
import logging
from message_handler import handle_star_gift

logger = logging.getLogger(__name__)

# --- Список чатов, которые нужно просматривать на историю ---
# ВАЖНО: Укажите здесь ID или юзернейм чата, который нужно "догнать" по истории
CHATS_TO_PROCESS_HISTORY = ['@kupil_prodal_l9m'] 


def register_gift_listener(client):
    """
    Подписка на ВСЕ НОВЫЕ сообщения (real-time).
    """
    @client.on(events.NewMessage)
    async def handle_new_gift(event):
        message = event.message
        action = getattr(message, 'action', None)
        if not action:
            return

        # Проверка по имени типа действия
        action_type = type(action).__name__
        if action_type == 'MessageActionStarGiftUnique':
            logger.info(f"🎁 (Real-Time) Новый NFT: {action_type} в чате {message.chat_id}")
            try:
                await handle_star_gift(message, client)
            except Exception as e:
                logger.error(f"⚠️ Ошибка при обработке нового NFT: {e}")


async def process_chat_history(client):
    """
    Проходит по истории указанных чатов, чтобы обработать старые/непрочитанные подарки.
    """
    for chat_identifier in CHATS_TO_PROCESS_HISTORY:
        logger.info(f"⏳ Начинаю обработку истории чата: {chat_identifier}...")
        
        try:
            chat_entity = await client.get_entity(chat_identifier)
        except Exception as e:
            logger.error(f"❌ Не удалось найти чат {chat_identifier}: {e}")
            continue

        processed_count = 0
        
        # Итерируем по всем сообщениям в чате (без лимита), начиная с конца
        async for message in client.iter_messages(chat_entity, reverse=True): 
            action = getattr(message, 'action', None)
            
            # 💡 Мы обрабатываем только StarGiftUnique
            if action and type(action).__name__ == 'MessageActionStarGiftUnique':
                processed_count += 1
                logger.warning(f"📜 (History) Найден NFT в MSG_ID: {message.id} в чате {chat_identifier}")
                try:
                    await handle_star_gift(message, client)
                except Exception as e:
                    logger.error(f"⚠️ Ошибка при обработке NFT из истории (MSG_ID: {message.id}): {e}")
            
            # Опционально: можно добавить ограничение по дате, чтобы не сканировать всю историю
            # if message.date < some_cutoff_date: break

        logger.info(f"✅ Обработка истории чата {chat_identifier} завершена. Найдено и обработано {processed_count} NFT.")