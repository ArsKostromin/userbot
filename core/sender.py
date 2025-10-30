import logging
from telethon import functions, types, errors

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    """
    Отправляет коллекционный подарок через официальный MTProto метод:
    payments.transferStarGift (вызов Telethon TL-функции).
    """

    logger.info("📦 Отправляю подарок через Telethon TL-функцию payments.transferStarGift ...")

    try:
        # 🧱 Конструируем аргументы строго по TL схеме
        request = functions.payments.TransferStarGiftRequest(
            stargift=types.InputSavedStarGiftUser(
                msg_id=gift_msg_id
            ),
            to_id=types.InputPeerUser(
                user_id=recipient_id,
                access_hash=recipient_hash
            )
        )

        # 🚀 Отправляем MTProto-вызов
        result = await client(request)

        logger.info("✅ Подарок успешно передан!")
        logger.info(f"Ответ Telegram: {result}")

        return result

    except errors.BadRequestError as e:
        msg = str(e)
        if "PAYMENT_REQUIRED" in msg:
            logger.error("❌ Недостаточно Stars (PAYMENT_REQUIRED)")
            logger.info(msg)
        elif "STARGIFT_NOT_FOUND" in msg:
            logger.error("❌ Указанный подарок (msg_id) не найден или больше недоступен.")
        elif "PEER_ID_INVALID" in msg:
            logger.error("❌ Неверный user_id или access_hash получателя.")
        else:
            logger.exception(f"❌ Неизвестная ошибка Telegram API: {msg}")
        return None

    except Exception as e:
        logger.exception(f"❌ Критическая ошибка при вызове payments.transferStarGift: {e}")
        return None
