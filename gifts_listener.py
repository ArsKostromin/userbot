from telethon import events, utils, functions
import logging
from message_handler import handle_star_gift

logger = logging.getLogger(__name__)

# ... (функция register_gift_listener остается без изменений)

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

        action_type = type(action).__name__
        if action_type == 'MessageActionStarGiftUnique':
            chat_name = utils.get_display_name(await event.get_chat())
            logger.info(f"🎁 (Real-Time) Новый NFT: {action_type} в чате '{chat_name}'")
            try:
                # Обрабатываем, отправляем на бэкенд, логируем
                await handle_star_gift(message, client)
                
                # Помечаем только это сообщение как прочитанное (для чистоты)
                await client(functions.messages.ReadMessageContentsRequest(
                    id=[message.id]
                ))

            except Exception as e:
                logger.error(f"⚠️ Ошибка при обработке нового NFT: {e}")


async def process_chat_history(client):
    """
    Проходит по истории ВСЕХ диалогов, обрабатывая ТОЛЬКО НЕПРОЧИТАННЫЕ сообщения
    с подарками, и помечает их как прочитанные после обработки.
    """
    logger.info("⏳ Начинаю обработку истории: ищем НЕПРОЧИТАННЫЕ NFT-подарки...")
    total_processed_gifts = 0
    total_scanned_chats = 0
    
    # Итерируем по всем диалогам
    async for dialog in client.iter_dialogs():
        chat_entity = dialog.entity
        chat_name = utils.get_display_name(chat_entity)
        processed_count = 0
        total_scanned_chats += 1
        
        # 1. Проверяем наличие непрочитанных сообщений в диалоге
        if dialog.unread_count == 0:
             continue
        
        # 💡 ИСПРАВЛЕНИЕ: Используем dialog.dialog.read_inbox_max_id
        # Если атрибута dialog нет (например, для некоторых служебных чатов),
        # используем 0, чтобы избежать ошибки.
        last_read_id = getattr(getattr(dialog, 'dialog', None), 'read_inbox_max_id', 0)
        
        logger.info(f"🔎 Сканирование НЕПРОЧИТАННОЙ истории чата: '{chat_name}' (Непрочитанных: {dialog.unread_count}, Last Read ID: {last_read_id})")

        processed_ids = []

        # Итерируем сообщения. Лимит 2000 для охвата недавних сообщений.
        async for message in client.iter_messages(chat_entity, limit=2000): 
            
            # ❗ ИСПРАВЛЕНИЕ УСЛОВИЯ: 
            # Прерываем итерацию, как только встречаем сообщение, которое явно старше 
            # или совпадает с последним известным прочитанным ID.
            if message.id <= last_read_id:
                 break
            
            action = getattr(message, 'action', None)
            
            if action and type(action).__name__ == 'MessageActionStarGiftUnique':
                processed_count += 1
                total_processed_gifts += 1
                
                logger.warning(f"📜 (Unread History) Найден NFT в MSG_ID: {message.id} в чате '{chat_name}'")
                
                try:
                    await handle_star_gift(message, client)
                    processed_ids.append(message.id)
                except Exception as e:
                    logger.error(f"⚠️ Ошибка при обработке NFT из истории (MSG_ID: {message.id}, Чат: {chat_name}): {e}")
        
        
        # 3. Помечаем все обработанные подарки (в этом чате) как прочитанные
        if processed_ids:
            try:
                # Отмечает сообщение как прочитанное для пользователя
                await client(functions.messages.ReadMessageContentsRequest(
                    id=processed_ids
                ))
                logger.info(f"☑️ Помечено как прочитанное {len(processed_ids)} NFT в чате '{chat_name}'.")
            except Exception as e:
                 logger.error(f"❌ Не удалось пометить сообщения {processed_ids} как прочитанные: {e}")

        
        logger.info(f"✅ Обработка непрочитанных сообщений в чате '{chat_name}' завершена. Найдено NFT: {processed_count}.")

    logger.info(f"🎉 Обработка истории завершена. Всего просканировано чатов: {total_scanned_chats}. Всего найдено NFT: {total_processed_gifts}.")
    