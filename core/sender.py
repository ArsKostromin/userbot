# core/sender.py
import logging
from telethon import functions, types, errors

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def send_snakebox_gift(client):
    """
    Тестируем MTProto raw вызовы через три способа:
    1. Telethon TL functions.*
    2. Прямой invoke(functions.*)
    3. Raw dict TL структура (чистый MTProto)
    """

    test_username = "test_snakebox_228"

    logger.info("🚀 Тестируем channels.checkUsername для имени: %s", test_username)

    # 🥇 1. Классический способ через Telethon TL-класс
    try:
        logger.info("🥇 Способ 1 — через functions.channels.CheckUsername")
        result1 = await client(functions.channels.CheckUsernameRequest(
            channel=types.InputChannel(
                channel_id=123456,  # поставь свой id канала если надо
                access_hash=0
            ),
            username=test_username
        ))
        logger.info(f"✅ Ответ (способ 1): {result1}")
    except Exception as e:
        logger.error(f"❌ Ошибка (способ 1): {e}")

    # 🥈 2. Через invoke() с TL объектом
    try:
        logger.info("🥈 Способ 2 — invoke(functions.channels.CheckUsernameRequest)")
        req = functions.channels.CheckUsernameRequest(
            channel=types.InputChannel(
                channel_id=123456,
                access_hash=0
            ),
            username=test_username
        )
        result2 = await client.invoke(req)
        logger.info(f"✅ Ответ (способ 2): {result2}")
    except Exception as e:
        logger.error(f"❌ Ошибка (способ 2): {e}")

    # 🥉 3. Через raw dict (настоящий MTProto “в лоб”)
    try:
        logger.info("🥉 Способ 3 — raw dict, pure MTProto")
        raw_request = {
            "_": "channels.checkUsername",
            "channel": {
                "_": "inputChannel",
                "channel_id": 123456,   # фейковый айди, просто для примера
                "access_hash": 0
            },
            "username": test_username
        }

        # invoke можно использовать только с TLObject, поэтому напрямую лезем в client._call
        result3 = await client._call(raw_request)
        logger.info(f"✅ Ответ (способ 3): {result3}")
    except Exception as e:
        logger.error(f"❌ Ошибка (способ 3): {e}")

    logger.info("🏁 Все три способа отработали — смотри, какой реально прошёл.")


# Пример использования:
# from telethon import TelegramClient
# client = TelegramClient('user', API_ID, API_HASH)
# await client.start()
# await send_snakebox_gift(client)
