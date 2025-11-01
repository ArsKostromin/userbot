# core/sender.py
import logging
from telethon import functions, types, errors
from telethon.tl.tlobject import TLObject  # ‼️ Убедись, что этот импорт есть

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ‼️ ‼️ ‼️
# ВЕРНИ ЭТОТ КЛАСС ОБРАТНО
# (Так как в telethon 1.41.2 его нет в 'types')
# ‼️ ‼️ ‼️
class InputPaymentCredentialsStars(TLObject):
    """
    TL-конструктор:
    inputPaymentCredentialsStars#bbf2dda0 flags:int = InputPaymentCredentials;
    """
    CONSTRUCTOR_ID = 0xbbf2dda0
    SUBCLASS_OF_ID = 0x3417d728  # InputPaymentCredentials

    def __init__(self, flags: int = 0):
        # В TL-схеме у него нет флагов, но в RPC-ответе от Telegram
        # (в 'form') он может прийти. 
        # Оставим flags=0, как ты и делал, это безопасно.
        self.flags = flags

    def to_dict(self):
        return {"_": "inputPaymentCredentialsStars", "flags": self.flags}

    def _bytes(self):
        # 4 байта конструктора + 4 байта флагов
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
            logger.info("✅ Подарок отправлен бесплатно (как выигранный)!")
            return result

        except errors.RPCError as e:
            if "PAYMENT_REQUIRED" not in str(e):
                logger.error(f"❌ Ошибка на этапе 1 (Transfer): {e}")
                raise
            logger.warning("💸 Подарок не 'выигран'. Требуется покупка за XTR — формируем инвойс...")

        # 2️⃣ Формируем invoice на ПОКУПКУ подарка
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
        #
        # ‼️ ИСПРАВЛЕНИЕ: Используем СВОЙ класс, а не types.
        #
        creds = InputPaymentCredentialsStars(flags=0)

        # 5️⃣ Отправляем форму оплаты
        logger.info("💳 Пытаемся оплатить форму с помощью XTR...")
        result = await client(functions.payments.SendPaymentFormRequest(
            form_id=form.form_id,
            invoice=invoice,
            credentials=creds  # <-- Теперь это твой кастомный класс
        ))

        logger.info("✅ Подарок успешно оплачен звёздами (XTR) и передан!")
        logger.info(f"Ответ Telegram: {result}")
        return result

    except errors.RPCError as e:
        if "FORM_UNSUPPORTED" in str(e):
            logger.critical("❌❌❌ ОШИБКА: FORM_UNSUPPORTED ❌❌❌")
            logger.critical("Это почти 100% означает, что у аккаунта юзербота НЕТ ЗВЁЗД (XTR) на балансе.")
            logger.critical("Пополните баланс (например, через @PremiumBot) и попробуйте снова.")
        else:
            logger.error(f"❌ RPC ошибка: {e.__class__.__name__} — {e}")
    except AttributeError as e:
        logger.error(f"❌ AttributeError (вероятно, ошибка в импорте): {e}")
    except Exception as e:
        logger.exception(f"💀 Критическая ошибка при отправке подарка: {e}")

    return None