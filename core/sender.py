# core/sender.py
import logging
from telethon import functions, types, errors

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 🛑 УБИРАЕМ ЭТОТ КЛАСС. Он больше не нужен.
# class InputPaymentCredentialsStars(TLObject):
#     ...

async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int):
    """
    Отправка подарка через MTProto (с поддержкой оплаты звёздами).
    """
    logger.info("📦 Проверяем, требует ли подарок оплату...")

    try:
        # 1️⃣ Пробуем бесплатный перевод
        # Это сработает, только если подарок был "выигран" (как в Змейке) и уже числится за юзером.
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
        # Если у юзербота ЕСТЬ XTR на балансе, эта форма будет ожидать оплату в XTR.
        # Если у юзербота НЕТ XTR, эта форма будет ожидать оплату в USD/EUR.
        form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))
        if not hasattr(form, "form_id"):
            raise ValueError("Не удалось получить form_id для оплаты")

        logger.info(f"🧾 Получена форма оплаты #{form.form_id} | Валюта: {form.invoice.currency}")

        # 4️⃣ Формируем корректный TL-конструктор
        # 
        # ‼️ ВОТ ГЛАВНОЕ ИСПРАВЛЕНИЕ В КОДЕ ‼️
        # Используем встроенный тип Telethon, а не самописный.
        #
        creds = types.InputPaymentCredentialsStars(flags=0)

        # 5️⃣ Отправляем форму оплаты
        #
        # ‼️ ВНИМАНИЕ ‼️
        # Если у юзербота на балансе 0 XTR, этот запрос ВСЕ РАВНО УПАДЕТ
        # с ошибкой FORM_UNSUPPORTED.
        #
        logger.info("💳 Пытаемся оплатить форму с помощью XTR...")
        result = await client(functions.payments.SendPaymentFormRequest(
            form_id=form.form_id,
            invoice=invoice,
            credentials=creds
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
    except Exception as e:
        logger.exception(f"💀 Критическая ошибка при отправке подарка: {e}")

    return None