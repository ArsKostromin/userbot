from telethon import events, utils, functions
import logging
from message_handler import handle_star_gift

logger = logging.getLogger(__name__)

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
             # Логируем только если нужно видеть, что чат пропущен
             # logger.debug(f"Skipping chat '{chat_name}': no unread messages.")
             continue
        
        logger.info(f"🔎 Сканирование НЕПРОЧИТАННОЙ истории чата: '{chat_name}' (Непрочитанных: {dialog.unread_count})")

        # 2. Итерируем сообщения, начиная с ID последнего прочитанного, чтобы минимизировать сканирование
        # 'limit=None' заставит нас скроллить до начала, но мы остановимся раньше.
        
        # NOTE: Telethon не имеет простого способа получить "только непрочитанные" сообщения.
        # Мы итерируем последние N сообщений (например, 2000), и обрабатываем, что найдем.
        # Более эффективный способ - использовать 'dialog.read_inbox_max_id' и итерировать с большим ID.
        
        # Для простоты и надежности, будем итерировать последние 2000 сообщений в чате, 
        # что должно охватить большинство новых непрочитанных подарков.
        
        processed_ids = []

        async for message in client.iter_messages(chat_entity, limit=2000): 
            # Если сообщение старее, чем последнее прочитанное, или оно уже прочитано - прерываем
            if message.id <= dialog.read_inbox_max_id:
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