# core/sender.py
import logging
from telethon import functions, types, errors
from telethon.tl.tlobject import TLObject

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class InputPaymentCredentialsStars(TLObject):
    """
    TL-конструктор:
    inputPaymentCredentialsStars#bbf2dda0 flags:int = InputPaymentCredentials;
    """
    CONSTRUCTOR_ID = 0xbbf2dda0
    SUBCLASS_OF_ID = 0x3417d728

    def __init__(self, flags: int = 0):
        self.flags = flags

    def to_dict(self):
        return {"_": "inputPaymentCredentialsStars", "flags": self.flags}

    def _bytes(self):
        # 4 байта конструктора + 4 байта флагов (0x00000000)
        return self.CONSTRUCTOR_ID.to_bytes(4, "little") + self.flags.to_bytes(4, "little")


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    """
    Отправка подарка через MTProto (с поддержкой оплаты звёздами).
    """
    logger.info("📦 Проверяем, требует ли подарок оплату...")

    try:
        # 1️⃣ Пробуем бесплатный перевод
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
            logger.warning("💸 Требуется оплата звёздами — формируем инвойс...")

        # 2️⃣ Формируем invoice
        invoice = types.InputInvoiceStarGiftTransfer(
            stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
            to_id=types.InputPeerUser(user_id=recipient_id, access_hash=recipient_hash)
        )

        # 3️⃣ Получаем форму оплаты
        form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))
        if not hasattr(form, "form_id"):
            raise ValueError("Не удалось получить form_id для оплаты")

        logger.info(f"🧾 Получена форма оплаты #{form.form_id} | Валюта: {form.invoice.currency}")

        # 4️⃣ Формируем корректный TL-конструктор
        creds = InputPaymentCredentialsStars(flags=0)

        # 5️⃣ Отправляем форму оплаты
        result = await client(functions.payments.SendPaymentFormRequest(
            form_id=form.form_id,
            invoice=invoice,
            credentials=creds
        ))

        logger.info("✅ Подарок успешно оплачен и передан!")
        logger.info(f"Ответ Telegram: {result}")
        return result

    except errors.RPCError as e:
        logger.error(f"❌ RPC ошибка: {e.__class__.__name__} — {e}")
    except Exception as e:
        logger.exception(f"💀 Критическая ошибка при отправке подарка: {e}")

    return None