import logging
from telethon import functions, types, errors
from telethon.tl.tlobject import TLObject

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class InputPaymentCredentialsStars(TLObject):
    """
    Конструктор Telegram для оплаты звёздами (XTR) напрямую со счёта.
    Используется в SendPaymentFormRequest, когда Telegram требует оплату.
    """
    CONSTRUCTOR_ID = 0xbbf2dda0
    SUBCLASS_OF_ID = 0x3417d728

    def __init__(self, flags: int = 0):
        self.flags = flags

    def to_dict(self):
        return {"_": "inputPaymentCredentialsStars", "flags": self.flags}

    def _bytes(self):
        return self.CONSTRUCTOR_ID.to_bytes(4, "little") + self.flags.to_bytes(4, "little")


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    """
    Отправка Telegram-подарка через MTProto с поддержкой оплаты звёздами (XTR).
    Если подарок бесплатный — сразу отправляем.
    Если требует оплату — создаём invoice и оплачиваем со счёта юзербота.
    """
    logger.info("Проверяем, требует ли подарок оплату...")

    try:
        # 1. Пытаемся отправить подарок бесплатно
        # (например, если это выигранный подарок — Telegram разрешит без оплаты)
        try:
            result = await client(functions.payments.TransferStarGiftRequest(
                stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
                to_id=types.InputPeerUser(user_id=recipient_id, access_hash=recipient_hash)
            ))
            logger.info("Подарок отправлен без оплаты")
            return result

        # 2. Если Telegram требует оплату — переходим к созданию инвойса
        except errors.RPCError as e:
            if "PAYMENT_REQUIRED" not in str(e):
                logger.error(f"Ошибка при бесплатной попытке: {e}")
                raise
            logger.warning("Требуется покупка подарка за XTR — создаём invoice...")

        # 3. Создаём invoice на покупку подарка
        # Telegram вернёт платёжную форму, которую потом можно оплатить звёздами
        invoice = types.InputInvoiceStarGiftTransfer(
            stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
            to_id=types.InputPeerUser(user_id=recipient_id, access_hash=recipient_hash)
        )

        # 4. Получаем форму оплаты по этому invoice
        form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))
        if not hasattr(form, "form_id"):
            raise ValueError("Не удалось получить form_id")

        logger.info(f"Получена форма оплаты #{form.form_id} | Валюта: {form.invoice.currency}")

        # 5. Создаём объект оплаты звёздами
        # Telegram использует TL-конструктор inputPaymentCredentialsStars
        creds = InputPaymentCredentialsStars(flags=0)

        # 6. Отправляем форму оплаты — Telegram спишет XTR и завершит транзакцию
        logger.info("Оплачиваем подарок звёздами...")
        result = await client(functions.payments.SendPaymentFormRequest(
            form_id=form.form_id,
            invoice=invoice,
            credentials=creds
        ))

        logger.info("Подарок успешно оплачен и отправлен!")
        logger.info(f"Ответ Telegram: {result}")
        return result

    # 7. Обработка ошибок Telegram API
    except errors.RPCError as e:
        if "FORM_UNSUPPORTED" in str(e):
            logger.critical("FORM_UNSUPPORTED — у юзербота нет XTR на балансе.")
        else:
            logger.error(f"RPC ошибка: {e.__class__.__name__} — {e}")

    # 8. Ошибка в импортах или структуре TL-объекта
    except AttributeError as e:
        logger.error(f"Ошибка структуры или импорта: {e}")

    # 9. Любая другая непредвиденная ошибка
    except Exception as e:
        logger.exception(f" Критическая ошибка при отправке подарка: {e}")

    return None
