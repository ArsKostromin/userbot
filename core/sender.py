import asyncio
import logging
from telethon import functions, types, errors

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def send_snakebox_gift(client):
    """
    Отправляет подарок "Snake Box" пользователю @jhgvcbcg (ID: 1207534564)
    через официальный метод Telethon (payments.transferStarGift).
    Совместим с telethon==1.41.2.

    ⚠️ Для collectible gifts требуется отдельная оплата Stars.
    """
    RECIPIENT_ID = 1207534564
    RECIPIENT_ACCESS_HASH = -8813161918532140746
    GIFT_MESSAGE_ID = 41


    req = functions.payments.TransferStarGift(
        stargift=types.InputSavedStarGiftUser(msg_id=GIFT_MESSAGE_ID),
        to_id=types.InputPeerUser(
            user_id=RECIPIENT_ID,
            access_hash=RECIPIENT_ACCESS_HASH
        )
    )

    logger.info("📦 Отправляю raw-MTProto запрос payments.transferStarGift ...")

    try:
        # Передаём TL-объект напрямую через invoke
        result = await client._call(req)  # напрямую через MTProtoSender
        logger.info(f"✅ Успешно: {result}")

    # !!!
    #  Перехват ошибок Telethon
    # !!!
    except errors.BadRequestError as e:
        err_msg = str(e)

        if "PAYMENT_REQUIRED" in err_msg:
            logger.error("❌ Недостаточно средств для отправки подарка (PAYMENT_REQUIRED)")
            logger.info("💡 Gift может быть collectible. Необходимо оплатить Stars через invoice:")
            logger.info("   1. Получить InputInvoiceStarGiftTransfer для этого подарка")
            logger.info("   2. Вызвать payments.getPaymentForm с этим invoice")
            logger.info("   3. Пройти оплату Stars через paymentFormStarGift")
            logger.info("   4. После успешной оплаты вызвать TransferStarGiftRequest снова")
        elif "STARGIFT_NOT_FOUND" in err_msg:
            logger.error("❌ Указанный подарок (Snake Box) не найден или больше недоступен.")
        elif "PEER_ID_INVALID" in err_msg:
            logger.error("❌ Неверный user_id или access_hash получателя.")
        else:
            logger.exception(f"❌ Неизвестная ошибка Telegram API: {err_msg}")

    except Exception as e:
        logger.exception(f"❌ Критическая ошибка при отправке подарка: {e}")
        raise