import asyncio
import logging
from telethon import events
from telethon.tl.types import MessageService

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


async def main():
    """
    Основная функция userbot'а
    Мониторит ВСЕ чаты на предмет Star Gifts, гифтов и обычных сообщений
    """
    client = create_client()

    try:
        if not await initialize_client(client):
            logger.error("❌ Не удалось инициализировать клиент")
            return

        logger.info("🔄 Userbot запущен и мониторит ВСЕ чаты на предмет Star Gifts и гифтов...")
        logger.info("💡 Для остановки нажмите Ctrl+C")

        # --- 1️⃣ Обычные текстовые сообщения --- говно
        @client.on(events.NewMessage)
        async def new_message_handler(event):
            await handle_new_message(event, client)

        # --- 2️⃣ Сервисные сообщения (где и приходят подарки) ---
        @client.on(events.Raw)
        async def raw_update_handler(event):
            try:
                # Если апдейт содержит message (в том числе MessageService)
                if hasattr(event, "message") and isinstance(event.message, MessageService):
                    logger.debug(f"📡 Сервисное сообщение: {type(event.message.action).__name__}")
                    await handle_new_message(event, client)
                # Иногда Telegram присылает пачку апдейтов
                elif hasattr(event, "updates"):
                    for update in event.updates:
                        if hasattr(update, "message") and isinstance(update.message, MessageService):
                            fake_event = type("FakeEvent", (), {"message": update.message})
                            await handle_new_message(fake_event, client)
            except Exception as e:
                logger.error(f"⚠️ Ошибка при обработке raw события: {e}")

        # --- 3️⃣ Запускаем вечный цикл ---
        await client.run_until_disconnected()

    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await client.disconnect()
        logger.info("👋 Userbot остановлен")


if __name__ == "__main__":
    asyncio.run(main())
