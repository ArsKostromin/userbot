# core/sender.py
import logging
from telethon import functions, types, errors

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    """
    Отправляет коллекционный подарок через MTProto.
    Использует уже инициализированного клиента Telethon.
    """
    logger.info("📦 Отправляю raw-MTProto запрос payments.transferStarGift ...")

    req = functions.payments.TransferStarGift(
        stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
        to_id=types.InputPeerUser(
            user_id=recipient_id,
            access_hash=recipient_hash
        )
    )

    try:
        # ВАЖНО: используем invoke, не _call — invoke это публичный метод
        result = await client.invoke(req)
        logger.info("✅ Подарок успешно передан!")
        logger.info(f"Ответ от Telegram: {result}")
        return result

    except errors.BadRequestError as e:
        err_msg = str(e)

        if "PAYMENT_REQUIRED" in err_msg:
            logger.error("❌ Недостаточно средств для отправки подарка (PAYMENT_REQUIRED).")
            logger.info("💡 Это collectible gift — нужно оплатить Stars.")
        elif "STARGIFT_NOT_FOUND" in err_msg:
            logger.error("❌ Указанный подарок (msg_id) не найден или больше недоступен.")
        elif "PEER_ID_INVALID" in err_msg:
            logger.error("❌ Неверный user_id или access_hash получателя.")
        else:
            logger.exception(f"❌ Неизвестная ошибка Telegram API: {err_msg}")
        return None

    except Exception as e:
        logger.exception(f"❌ Критическая ошибка при отправке подарка: {e}")
        return None
