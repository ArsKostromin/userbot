import asyncio
import logging
from telethon import events

from config import TARGET_CHAT_USERNAME, LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from telegram_client import create_client, initialize_client
from message_handler import handle_new_message

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL),
    datefmt=LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)

# --- ОСНОВНАЯ ФУНКЦИЯ ---

async def main():
    # Создаем клиент
    client = create_client()
    
    async with client:
        # Инициализируем клиент
        if not await initialize_client(client):
            return
        
        try:
            logger.info(f"🔎 Ищем чат: {TARGET_CHAT_USERNAME}...")
            chat = await client.get_entity(TARGET_CHAT_USERNAME)
            chat_name = getattr(chat, 'title', getattr(chat, 'username', str(chat.id)))
            logger.info(f"👍 Чат '{chat_name}' найден. Начинаю мониторинг новых сообщений...")

        except Exception as e:
            logger.error(f"❌ Произошла непредвиденная ошибка при поиске чата: {e}")
            return

        # Регистрируем обработчик новых сообщений
        @client.on(events.NewMessage)
        async def new_message_handler(event):
            await handle_new_message(event, chat, client)
        
        logger.info("🔄 Userbot запущен и мониторит новые сообщения...")
        logger.info("💡 Для остановки нажмите Ctrl+C")
        
        # Запускаем мониторинг (будет работать до остановки)
        await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())