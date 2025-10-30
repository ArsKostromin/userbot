# core/sender.py
import logging
from telethon import types, errors
from telethon.tl import custom

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    """
    Передаёт подарок через raw MTProto вызов (TransferStarGift),
    даже если Telethon не содержит автогенерированного метода.
    """
    logger.info("📦 Отправляю raw-MTProto запрос payments.transferStarGift (raw) ...")

    # Ручная упаковка запроса (API ID = 0xdeadbeef — фейк, заменяется автоматически)
    body = {
        "_": "payments.transferStarGift",
        "stargift": {
            "_": "inputSavedStarGiftUser",
            "msg_id": gift_msg_id
        },
        "to_id": {
            "_": "inputPeerUser",
            "user_id": recipient_id,
            "access_hash": recipient_hash
        }
    }

    try:
        result = await client._call(body)
        logger.info("✅ Подарок успешно передан (через raw invoke)!")
        logger.info(f"Ответ от Telegram: {result}")
        return result

    except errors.BadRequestError as e:
        msg = str(e)
        if "PAYMENT_REQUIRED" in msg:
            logger.error("❌ Недостаточно Stars (PAYMENT_REQUIRED)")
        elif "STARGIFT_NOT_FOUND" in msg:
            logger.error("❌ Указанный подарок не найден или недоступен")
        elif "PEER_ID_INVALID" in msg:
            logger.error("❌ Неверный user_id / access_hash")
        else:
            logger.exception(f"❌ Неизвестная ошибка Telegram API: {msg}")

    except Exception as e:
        logger.exception(f"❌ Критическая ошибка при raw-вызове: {e}")
