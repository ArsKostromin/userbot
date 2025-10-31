# core/sender.py
import logging
from telethon import functions, types, errors
from telethon.tl.tlobject import TLObject

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class InputPaymentCredentialsStars(TLObject):
    """
    Ручная реализация TL-конструктора:
    inputPaymentCredentialsStars#bbf2dda0 = InputPaymentCredentials;
    """
    CONSTRUCTOR_ID = 0xbbf2dda0
    SUBCLASS_OF_ID = 0x3417d728  # общий ID InputPaymentCredentials

    def __init__(self):
        pass

    def to_dict(self):
        """Для отладки — возвращает TL-представление"""
        return {"_": "inputPaymentCredentialsStars"}

    def _bytes(self):
        """Возвращает 4 байта конструктора (raw MTProto)"""
        return self.CONSTRUCTOR_ID.to_bytes(4, "little")


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    """
    Отправляет подарок через MTProto.
    Шаги:
      1. Пробует бесплатную передачу (payments.transferStarGift)
      2. Если требуется оплата, получает форму (payments.getPaymentForm)
      3. Отправляет оплату с inputPaymentCredentialsStars
    """

    logger.info("📦 Проверяем, требует ли подарок оплату...")

    try:
        # 🥇 Попытка бесплатного перевода
        try:
            result = await client(functions.payments.TransferStarGiftRequest(
                stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
                to_id=types.InputPeerUser(
                    user_id=recipient_id,
                    access_hash=recipient_hash
                )
            ))
            logger.info("✅ Подарок успешно передан без оплаты!")
            return result

        except errors.RPCError as e:
            if "PAYMENT_REQUIRED" not in str(e):
                raise
            logger.warning("💸 Требуется оплата звёздами — формируем инвойс...")

        # 🥈 Формируем invoice для подарка
        invoice = types.InputInvoiceStarGiftTransfer(
            stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
            to_id=types.InputPeerUser(
                user_id=recipient_id,
                access_hash=recipient_hash
            )
        )

        # 🥉 Получаем форму оплаты
        form = await client(functions.payments.GetPaymentFormRequest(
            invoice=invoice
        ))

        if not hasattr(form, "form_id"):
            raise ValueError("Не удалось получить form_id (форма оплаты пустая)")

        logger.info(f"🧾 Получена форма оплаты #{form.form_id} | Валюта: {form.invoice.currency}")

        # 🧠 Создаём TL-конструктор для Stars
        creds = InputPaymentCredentialsStars()

        # 🚀 Отправляем форму оплаты
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
