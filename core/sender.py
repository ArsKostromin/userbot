# core/sender.py
import logging
from telethon import functions, errors

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def send_snakebox_gift(client):
    """
    Тестируем MTProto вызов (help.getNearestDc) через три способа:
    1. Telethon TL functions.* — await client(function)
    2. Прямой invoke / _invoke_with_layer (ручной TL)
    3. Raw dict через client._sender.send()
    """

    logger.info("🚀 Тестируем MTProto методы (help.getNearestDc)")

    # 🥇 1. Классический способ через Telethon TL-функцию
    try:
        logger.info("🥇 Способ 1 — await client(functions.help.GetNearestDcRequest())")
        result1 = await client(functions.help.GetNearestDcRequest())
        logger.info(f"✅ Ответ (способ 1): {result1}")
    except Exception as e:
        logger.error(f"❌ Ошибка (способ 1): {e}")

    # 🥈 2. Через внутренний invoke_with_layer
    try:
        logger.info("🥈 Способ 2 — _invoke_with_layer(214, TLObject)")
        request = functions.help.GetNearestDcRequest()
        result2 = await client._invoke_with_layer(214, request)
        logger.info(f"✅ Ответ (способ 2): {result2}")
    except Exception as e:
        logger.error(f"❌ Ошибка (способ 2): {e}")

    # 🥉 3. Через raw dict (чистый MTProto “в лоб”)
    try:
        logger.info("🥉 Способ 3 — raw dict через client._sender.send()")
        raw_request = {"_": "help.getNearestDc"}
        result3 = await client._sender.send(raw_request)
        logger.info(f"✅ Ответ (способ 3): {result3}")
    except Exception as e:
        logger.error(f"❌ Ошибка (способ 3): {e}")

    logger.info("🏁 Все три способа отработали — смотри, какой реально прошёл.")

# from telethon import TelegramClient
# client = TelegramClient('user', API_ID, API_HASH)
# await client.start()
# await send_snakebox_gift(client)
