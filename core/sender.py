import logging
from telethon import functions, types, errors
from telethon.tl.types import InputPaymentCredentials


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class InputPaymentCredentialsStars(InputPaymentCredentials):
    """
    TL-тип:
    inputPaymentCredentialsStars#bbf2dda0 = InputPaymentCredentials;
    """
    CONSTRUCTOR_ID = 0xbbf2dda0
    SUBCLASS_OF_ID = 0x3417d728  # общий ID для InputPaymentCredentials

    def __init__(self):
        pass

    def to_dict(self):
        return {"_": "inputPaymentCredentialsStars"}

    def _bytes(self):
        # TL-конструктор без полей → возвращаем только ID
        return self.CONSTRUCTOR_ID.to_bytes(4, "little")

async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    logger.info("📦 Проверяем, требует ли подарок оплату...")

    try:
        # 1️⃣ Пробуем отправить напрямую
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

        # 2️⃣ Создаём invoice для оплаты
        invoice = types.InputInvoiceStarGiftTransfer(
            stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
            to_id=types.InputPeerUser(user_id=recipient_id, access_hash=recipient_hash)
        )

        # 3️⃣ Получаем форму оплаты
        form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))
        logger.info(f"🧾 Получили форму оплаты: {form}")

        # 4️⃣ Используем наш кастомный TLObject вместо словаря
        creds = InputPaymentCredentialsStars()

        # 5️⃣ Отправляем оплату
        result = await client(functions.payments.SendPaymentFormRequest(
            form_id=form.form_id,
            invoice=invoice,
            credentials=creds
        ))

        logger.info("✅ Подарок успешно оплачен и передан!")
        logger.info(f"Ответ Telegram: {result}")
        return result

    except Exception as e:
        logger.exception(f"💀 Критическая ошибка при отправке подарка: {e}")
        return None
