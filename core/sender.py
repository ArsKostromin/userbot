import logging
from telethon import functions, types, errors
from telethon.tl import TLObject

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class InputPaymentCredentialsStars(TLObject):
    """
    TL-конструктор:
    inputPaymentCredentialsStars#bbf2dda0 = InputPaymentCredentials;
    """
    CONSTRUCTOR_ID = 0xbbf2dda0
    SUBCLASS_OF_ID = 0x3417d728  # общий ID для InputPaymentCredentials

    def __init__(self):
        pass

    def to_dict(self):
        return {"_": "inputPaymentCredentialsStars"}

    def _bytes(self):
        return self.CONSTRUCTOR_ID.to_bytes(4, "little")


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    """
    Передача подарка через MTProto (Telethon)
    — сначала пытаемся бесплатным способом через payments.transferStarGift,
    — если требуется оплата звёздами, используем payments.getPaymentForm + payments.sendPaymentForm.
    """
    logger.info("📦 Проверяем, требует ли подарок оплату...")

    try:
        # 1️⃣ Пробуем бесплатный трансфер
        try:
            result = await client(functions.payments.TransferStarGiftRequest(
                stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
                to_id=types.InputPeerUser(user_id=recipient_id, access_hash=recipient_hash)
            ))
            logger.info("✅ Подарок отправлен без оплаты!")
            return result
        except errors.RPCError as e:
            if "PAYMENT_REQUIRED" not in str(e):
                raise
            logger.warning("💸 Требуется оплата звёздами, готовим инвойс...")

        # 2️⃣ Формируем инвойс
        invoice = types.InputInvoiceStarGiftTransfer(
            stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
            to_id=types.InputPeerUser(user_id=recipient_id, access_hash=recipient_hash)
        )

        # 3️⃣ Получаем форму оплаты
        form = await client(functions.payments.GetPaymentFormRequest(
            invoice=invoice
        ))

        if not hasattr(form, "form_id"):
            raise ValueError("Не удалось получить form_id для оплаты")

        logger.info(f"🧾 Получена форма оплаты #{form.form_id}, валюта: {form.invoice.currency}")

        # 4️⃣ Создаём TL-конструктор для Telegram Stars
        creds = InputPaymentCredentialsStars()

        # 5️⃣ Оплачиваем и передаём подарок
        result = await client(functions.payments.SendPaymentFormRequest(
            form_id=form.form_id,
            invoice=invoice,
            credentials=creds
        ))

        logger.info("✅ Подарок успешно оплачен и передан!")
        logger.info(f"Ответ Telegram: {result}")
        return result

    except errors.RPCError as e:
        logger.error(f"❌ RPC ошибка: {e.__class__.__name__}: {e}")
    except Exception as e:
        logger.exception(f"💀 Критическая ошибка при отправке подарка: {e}")

    return None
