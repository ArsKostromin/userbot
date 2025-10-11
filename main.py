import asyncio
import logging
from telethon import events

from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
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
    """
    Основная функция userbot'а
    Мониторит ВСЕ чаты на предмет Star Gifts
    """
    # Создаем Telegram клиент
    client = create_client()
    
    try:
        # Инициализируем клиент (подключаемся и проверяем авторизацию)
        if not await initialize_client(client):
            logger.error("❌ Не удалось инициализировать клиент")
            return
        
        logger.info("🔄 Userbot запущен и мониторит ВСЕ чаты на предмет Star Gifts...")
        logger.info("💡 Для остановки нажмите Ctrl+C")
        
        # Регистрируем обработчик новых сообщений для ВСЕХ чатов
        # Логика обработки сообщений находится в файле: message_handler.py
        @client.on(events.NewMessage)
        async def new_message_handler(event):
            # Передаем только client, так как теперь мониторим все чаты
            await handle_new_message(event, client)
        
        # Запускаем мониторинг (будет работать до остановки)
        await client.run_until_disconnected()
        
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        # Отключаемся от Telegram
        await client.disconnect()
        logger.info("👋 Userbot остановлен")

if __name__ == "__main__":
    asyncio.run(main())