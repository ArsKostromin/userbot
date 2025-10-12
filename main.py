import asyncio
import logging

# Предполагаем, что config, telegram_client и message_handler существуют
from config import LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL
from telegram_client import create_client, initialize_client
from gifts_listener import register_gift_listener, process_chat_history # Импортируем новую функцию

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    format=LOG_FORMAT,
    level=getattr(logging, LOG_LEVEL),
    datefmt=LOG_DATE_FORMAT
)
logger = logging.getLogger(__name__)


async def main():
    """
    Userbot, который мониторит ВСЕ новые сообщения и обрабатывает историю.
    """
    client = create_client()

    try:
        if not await initialize_client(client):
            logger.error("❌ Не удалось инициализировать клиент")
            return

        # 1. ОБРАБОТКА ИСТОРИИ: Проходим по всем старым/непрочитанным сообщениям
        # ВНИМАНИЕ: Это должно быть выполнено один раз при запуске, чтобы "догнать" историю.
        await process_chat_history(client)

        # 2. REAL-TIME МОНИТОРИНГ: Подключаем listener для новых сообщений
        register_gift_listener(client)

        logger.info("🔄 Userbot запущен. Мониторит все чаты в реальном времени...")
        logger.info("💡 Для остановки нажмите Ctrl+C")

        # --- Запускаем вечный цикл для real-time listener ---
        await client.run_until_disconnected()

    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки...")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
    finally:
        await client.disconnect()
        logger.info("👋 Userbot остановлен")


if __name__ == "__main__":
    # Убедитесь, что ваш файл config.py содержит необходимые константы
    # (LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL)
    asyncio.run(main())