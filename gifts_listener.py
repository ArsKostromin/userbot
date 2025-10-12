from telethon import events, utils
import logging
from message_handler import handle_star_gift

logger = logging.getLogger(__name__)

# --- Список чатов, которые нужно просматривать на историю ---
# УДАЛЯЕМ статический список CHATS_TO_PROCESS_HISTORY
# CHATS_TO_PROCESS_HISTORY = ['@kupil_prodal_l9m'] 

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
            # Получаем читабельное имя чата для лога
            chat_name = utils.get_display_name(await event.get_chat())
            logger.info(f"🎁 (Real-Time) Новый NFT: {action_type} в чате '{chat_name}'")
            try:
                await handle_star_gift(message, client)
            except Exception as e:
                logger.error(f"⚠️ Ошибка при обработке нового NFT: {e}")


async def process_chat_history(client):
    """
    Проходит по истории ВСЕХ диалогов (чатов, групп, каналов) для обработки 
    старых/непрочитанных подарков.
    """
    logger.info("⏳ Начинаю обработку истории ВСЕХ чатов...")
    total_processed_gifts = 0
    total_processed_chats = 0

    # 1. Итерируем по всем диалогам (чатам, группам, каналам)
    async for dialog in client.iter_dialogs():
        chat_entity = dialog.entity
        chat_name = utils.get_display_name(chat_entity)
        processed_count = 0
        total_processed_chats += 1

        # Пропускаем личные диалоги, если не хотите их сканировать, или если это не группа/канал
        # if dialog.is_user: continue 
        
        logger.info(f"🔎 Сканирование истории чата: '{chat_name}' (ID: {dialog.id})")

        # 2. Итерируем по всем сообщениям в текущем чате (без лимита), начиная с конца
        async for message in client.iter_messages(chat_entity, reverse=True): 
            action = getattr(message, 'action', None)
            
            # Мы обрабатываем только StarGiftUnique
            if action and type(action).__name__ == 'MessageActionStarGiftUnique':
                processed_count += 1
                total_processed_gifts += 1
                logger.warning(f"📜 (History) Найден NFT в MSG_ID: {message.id} в чате '{chat_name}'")
                try:
                    await handle_star_gift(message, client)
                except Exception as e:
                    logger.error(f"⚠️ Ошибка при обработке NFT из истории (MSG_ID: {message.id}, Чат: {chat_name}): {e}")
            
            # Ограничение: Если чат слишком большой, можно ограничить количество сообщений для сканирования 
            # if message.id < (dialog.message.id - 10000): break # Например, не читать старее 10000 сообщений

        logger.info(f"✅ Обработка чата '{chat_name}' завершена. Найдено NFT: {processed_count}.")

    logger.info(f"🎉 Обработка истории завершена. Всего просканировано чатов: {total_processed_chats}. Всего найдено NFT: {total_processed_gifts}.")