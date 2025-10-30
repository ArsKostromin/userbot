async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int, saved_payment_method_id: int):
    """
    Отправка Star Gift платным способом через существующий сохранённый способ оплаты.
    """
    try:
        logger.info("💸 Формируем инвойс для оплаты звёздами...")

        # 1️⃣ Создаём инвойс для подарка
        invoice = types.InputInvoiceStarGiftTransfer(
            stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
            to_id=types.InputPeerUser(user_id=recipient_id, access_hash=recipient_hash)
        )

        # 2️⃣ Получаем форму оплаты от сервера
        form = await client(functions.payments.GetPaymentFormRequest(invoice=invoice))

        if not hasattr(form, "form_id"):
            raise ValueError("Не удалось получить form_id для оплаты")

        logger.info(f"🧾 Получена форма оплаты #{form.form_id}, валюта: {form.invoice.currency}")

        # 3️⃣ Используем реальный TLObject для сохранённого способа оплаты
        creds = types.InputPaymentCredentialsSaved(
            saved_payment_method_id=int(saved_payment_method_id)
        )

        # 4️⃣ Отправляем форму платежа
        result = await client(functions.payments.SendPaymentFormRequest(
            form_id=form.form_id,
            invoice=form.invoice,  # используем именно форму, вернувшуюся от сервера
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
