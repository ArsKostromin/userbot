import logging
from telethon import functions, types, errors
from telethon.tl.tlobject import TLObject
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


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


async def send_gift_to_user(
    client,
    gift_id: int,
    recipient_telegram_id: int,
    peer_id: Optional[int] = None,
    msg_id: Optional[int] = None,
    access_hash: Optional[int] = None
) -> Dict[str, Any]:
    """
    Отправляет подарок пользователю по запросу из Django API.
    
    Args:
        client: Telethon клиент
        gift_id: ID подарка в Django БД
        recipient_telegram_id: Telegram ID получателя
        peer_id: ID чата где лежит подарок (опционально)
        msg_id: ID сообщения с подарком (опционально)
        access_hash: Access hash чата (опционально)
    
    Returns:
        Dict с результатом отправки
    """
    logger.info(f"🎁 Отправка подарка ID={gift_id} пользователю {recipient_telegram_id}")
    
    try:
        # Получаем access_hash получателя
        try:
            recipient_entity = await client.get_entity(recipient_telegram_id)
            recipient_hash = getattr(recipient_entity, 'access_hash', None)
            if not recipient_hash:
                logger.error(f"❌ Не удалось получить access_hash для пользователя {recipient_telegram_id}")
                return {
                    "status": "error",
                    "error": f"Не удалось получить access_hash для пользователя {recipient_telegram_id}"
                }
        except Exception as e:
            logger.error(f"❌ Ошибка при получении entity пользователя {recipient_telegram_id}: {e}")
            return {
                "status": "error",
                "error": f"Не удалось найти пользователя {recipient_telegram_id}: {str(e)}"
            }
        
        # Если есть msg_id, используем его для отправки
        if msg_id:
            logger.info(f"📨 Используем сохранённый msg_id={msg_id} для отправки подарка")
            result = await send_snakebox_gift(
                client=client,
                recipient_id=recipient_telegram_id,
                recipient_hash=recipient_hash,
                gift_msg_id=msg_id
            )
        else:
            # Пытаемся найти подарок в сохранённых подарках пользователя
            # Для этого нужно получить список сохранённых подарков
            logger.warning("⚠️ msg_id не указан, попытка найти подарок в сохранённых...")
            # TODO: Реализовать поиск подарка по gift_id в сохранённых подарках
            # Пока возвращаем ошибку
            return {
                "status": "error",
                "error": "msg_id не указан и поиск в сохранённых подарках не реализован"
            }
        
        if result:
            if isinstance(result, dict) and result.get("status") == "payment_required":
                return {
                    "status": "payment_required",
                    "data": result
                }
            else:
                return {
                    "status": "success",
                    "message": "Подарок успешно отправлен",
                    "data": result
                }
        else:
            return {
                "status": "error",
                "error": "Неизвестная ошибка при отправке подарка"
            }
            
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка при отправке подарка: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
