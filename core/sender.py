import logging
from telethon import functions, types, errors

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    logger.info("📦 Проверяем, требует ли подарок оплату...")

    try:
        # Шаг 1 — пробуем прямой трансфер (если бесплатный)
        try:
            result = await client(functions.payments.TransferStarGiftRequest(
                stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
                to_id=types.InputPeerUser(
                    user_id=recipient_id,
                    access_hash=recipient_hash
                )
            ))
            logger.info("✅ Подарок успешно отправлен без оплаты!")
            return result

        except errors.RPCError as e:
            if "PAYMENT_REQUIRED" not in str(e):
                raise
            logger.warning("💸 Требуется оплата звёздами, готовим инвойс...")

        # Шаг 2 — invoice для оплаты transfer
        invoice = types.InputInvoiceStarGiftTransfer(
            stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
            to_id=types.InputPeerUser(
                user_id=recipient_id,
                access_hash=recipient_hash
            )
        )

        # Шаг 3 — получаем форму оплаты
        form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))
        logger.info(f"🧾 Получили форму оплаты: {form}")

        # 🧠 Telethon не знает InputPaymentCredentialsStars, делаем raw dict
        input_creds_stars = {"_": "inputPaymentCredentialsStars"}

        # Шаг 4 — отправляем оплату (чистый MTProto)
        result = await client(functions.payments.SendPaymentFormRequest(
            form_id=form.form_id,
            invoice=invoice,
            requested_info_id=None,
            shipping_option_id=None,
            credentials=input_creds_stars
        ))

        logger.info("✅ Подарок успешно оплачен и передан!")
        logger.info(f"Ответ Telegram: {result}")
        return result

    except errors.RPCError as e:
        msg = str(e)
        if "STARGIFT_NOT_FOUND" in msg:
            logger.error("❌ Указанный подарок не найден или больше недоступен.")
        elif "PEER_ID_INVALID" in msg:
            logger.error("❌ Неверный user_id или access_hash получателя.")
        elif "STARGIFT_OWNER_INVALID" in msg:
            logger.error("❌ Этот подарок не принадлежит текущему аккаунту.")
        elif "STARGIFT_TRANSFER_TOO_EARLY" in msg:
            logger.error("⏳ Подарок пока нельзя перевести (время блокировки не прошло).")
        else:
            logger.exception(f"❌ Ошибка Telegram API: {msg}")
        return None

    except Exception as e:
        logger.exception(f"💀 Критическая ошибка при отправке подарка: {e}")
        return None
