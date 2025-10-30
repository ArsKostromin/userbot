import logging
from telethon import errors

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    """
    Отправляет коллекционный подарок через raw MTProto.
    Использует invoke с TL-сырой структурой, как описано в:
    https://docs.telethon.dev/en/stable/concepts/full-api.html#invoking-raw-methods
    """

    logger.info("📦 Отправляю raw-MTProto запрос payments.transferStarGift ...")

    # TL-сырой запрос — точно по спецификации Telegram
    raw_request = {
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
        # 🧠 Ключевое — invoke, не _call!
        result = await client.invoke(raw_request)
        logger.info("✅ Подарок успешно передан!")
        logger.info(f"Ответ Telegram: {result}")
        return result

    except errors.BadRequestError as e:
        msg = str(e)
        if "PAYMENT_REQUIRED" in msg:
            logger.error("❌ Недостаточно Stars (PAYMENT_REQUIRED)")
            logger.info("💡 Gift, скорее всего, collectible — нужно оплатить Stars через invoice.")
        elif "STARGIFT_NOT_FOUND" in msg:
            logger.error("❌ Указанный подарок (msg_id) не найден или больше недоступен.")
        elif "PEER_ID_INVALID" in msg:
            logger.error("❌ Неверный user_id или access_hash получателя.")
        else:
            logger.exception(f"❌ Неизвестная ошибка Telegram API: {msg}")
        return None

    except Exception as e:
        logger.exception(f"❌ Критическая ошибка при raw-вызове: {e}")
        return None
