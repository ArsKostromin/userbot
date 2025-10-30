import logging
from telethon import functions, types, errors
from telethon.tl import TLObject
from telethon.utils import pack_bytes

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# 🔧 Мини-класс для InputPaymentCredentialsStars (так как Telethon его не знает)
class InputPaymentCredentialsStars(TLObject):
    CONSTRUCTOR_ID = 0xbbf2dda0  # тот самый из TL схемы
    SUBCLASS_OF_ID = 0x1aa3e617  # общий ID InputPaymentCredentials

    def __init__(self):
        pass

    def to_dict(self):
        return {"_": "inputPaymentCredentialsStars"}

    def _bytes(self):
        # просто сериализуем конструктор без аргументов
        return pack_bytes(self.CONSTRUCTOR_ID)


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    logger.info("📦 Проверяем, требует ли подарок оплату...")

    try:
        try:
            # 🔹 Сначала пробуем отправить подарок напрямую
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

        # 🔹 Создаём invoice для оплаты
        invoice = types.InputInvoiceStarGiftTransfer(
            stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
            to_id=types.InputPeerUser(
                user_id=recipient_id,
                access_hash=recipient_hash
            )
        )

        # 🔹 Получаем форму оплаты
        form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))
        logger.info(f"🧾 Получили форму оплаты: {form}")

        # 🔹 Создаём “raw” объект credentials — но корректный TLObject
        creds = InputPaymentCredentialsStars()

        # 🔹 Отправляем оплату
        result = await client(functions.payments.SendPaymentFormRequest(
            form_id=form.form_id,
            invoice=invoice,
            requested_info_id=None,
            shipping_option_id=None,
            credentials=creds
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
