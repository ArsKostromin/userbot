import logging
from telethon import functions, types, errors
from telethon.tl.tlobject import TLObject
from typing import Optional, Dict, Any, Union

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


async def find_gift_msg_id_by_external_id(client, gift_id_external: int) -> Optional[int]:
    """
    Ищет внутренний ID сообщения (msg_id) подарка в инвентаре Userbot
    на основе внешнего ID (например, ID из вашей БД).
    
    ВНИМАНИЕ: Для работы необходимо реализовать логику сопоставления.
    В данном примере мы ПРЕДПОЛАГАЕМ, что внешний ID совпадает с msg_id.
    Если это не так, вам нужно будет парсить метаданные (messageActionStarGiftUnique) 
    каждого подарка в цикле.
    """
    logger.info(f"🔎 Запрос инвентаря. Поиск msg_id для внешнего ID={gift_id_external}...")
    try:
        # Запрашиваем инвентарь подарков Userbot (максимальный лимит 1000)
        inventory_result = await client(functions.payments.GetSavedStarGiftsRequest(
            offset=0,
            limit=1000 
        ))

        for gift_struct in inventory_result.gifts:
            # gift_struct - это SavedStarGiftUser или SavedStarGiftChat
            
            # --- ВАША ЛОГИКА СОПОСТАВЛЕНИЯ ЗДЕСЬ ---
            # Предположим, что внешний ID совпадает с внутренним msg_id:
            if hasattr(gift_struct, 'msg_id') and gift_struct.msg_id == gift_id_external:
                logger.info(f"✅ Найден подарок: msg_id={gift_struct.msg_id} (совпадает с внешним ID).")
                return gift_struct.msg_id
            
            # Если вам нужно парсить другие поля (например, slug, name) для сопоставления:
            # if gift_struct.gift.slug == str(gift_id_external):
            #     return gift_struct.msg_id

        logger.warning(f"❌ Подарок с внешним ID={gift_id_external} не найден в инвентаре.")
        return None

    except errors.RPCError as e:
        logger.error(f"❌ Ошибка RPC при получении инвентаря: {e.__class__.__name__} — {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при поиске подарка: {e}")
        return None


async def send_snakebox_gift(client, recipient_id: int, recipient_hash: int, gift_msg_id: int) -> Union[Any, None]:
    """
    Отправка Telegram-подарка через MTProto с поддержкой оплаты звёздами (XTR).
    Включает логику для покупки подарка, если это требуется.
    """
    logger.info("Проверяем, требует ли подарок оплату...")

    try:
        # 1. Пытаемся отправить подарок бесплатно
        result = await client(functions.payments.TransferStarGiftRequest(
            stargift=types.InputSavedStarGiftUser(msg_id=gift_msg_id),
            to_id=types.InputPeerUser(user_id=recipient_id, access_hash=recipient_hash)
        ))
        logger.info("Подарок отправлен без оплаты")
        return result

    # 2. Если Telegram требует оплату, или подарок не найден (ошибки RPC)
    except errors.RPCError as e:
        if "PAYMENT_REQUIRED" in str(e):
            logger.warning("Требуется покупка подарка за XTR — создаём invoice...")

            # 3. Создаём invoice на покупку подарка
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
            creds = InputPaymentCredentialsStars(flags=0)

            # 6. Отправляем форму оплаты — Telegram спишет XTR и завершит транзакцию
            logger.info("Оплачиваем подарок звёздами...")
            result = await client(functions.payments.SendPaymentFormRequest(
                form_id=form.form_id,
                invoice=invoice,
                credentials=creds
            ))

            logger.info("Подарок успешно оплачен и отправлен!")
            return result
            
        elif "STARGIFT_NOT_FOUND" in str(e):
            logger.error(f"❌ STARGIFT_NOT_FOUND: Подарок (msg_id={gift_msg_id}) не найден в инвентаре.")
            # Явная обработка ошибки для эндпоинта
            return {"status": "error", "error": "Подарок не найден или уже был отправлен."} 
        
        else:
            logger.error(f"Ошибка при бесплатной попытке: {e.__class__.__name__} — {e}")
            raise

    except Exception as e:
        logger.exception(f" Критическая ошибка при отправке подарка: {e}")
        return None


async def send_gift_to_user(
    client,
    gift_id_external: int,
    recipient_telegram_id: int,
    gift_msg_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Отправляет подарок пользователю по внешнему ID или msg_id.
    
    Args:
        client: Telethon клиент (Userbot)
        gift_id_external: ID подарка из вашей БД (используется для поиска msg_id)
        recipient_telegram_id: Telegram ID получателя
        gift_msg_id: ID сообщения с подарком (если известен)
    
    Returns:
        Dict с результатом отправки
    """
    logger.info(f"🎁 Отправка подарка ID={gift_id_external} пользователю {recipient_telegram_id}")
    
    try:
        # 1. Получаем access_hash получателя (критически важно для MTProto)
        try:
            # client.get_entity сам разрешает access_hash
            recipient_entity = await client.get_entity(recipient_telegram_id)
            recipient_hash = getattr(recipient_entity, 'access_hash', None)
            
            if not recipient_hash:
                logger.error(f"❌ Не удалось получить access_hash для пользователя {recipient_telegram_id}")
                return {
                    "status": "error",
                    "error": f"Не удалось получить access_hash для пользователя {recipient_telegram_id}. Возможно, пользователь неактивен."
                }
        except Exception as e:
            logger.error(f"❌ Ошибка при получении entity пользователя {recipient_telegram_id}: {e}")
            return {
                "status": "error",
                "error": f"Не удалось найти пользователя {recipient_telegram_id}: {str(e)}"
            }
        
        # 2. Определяем msg_id
        final_msg_id = gift_msg_id
        if not final_msg_id:
            # Если msg_id не передан, ищем его по внешнему ID
            final_msg_id = await find_gift_msg_id_by_external_id(client, gift_id_external)
        
        if not final_msg_id:
            return {
                "status": "error",
                "error": f"Не удалось определить msg_id для подарка с ID={gift_id_external}. Поиск не дал результатов."
            }

        logger.info(f"📨 Используем msg_id={final_msg_id} для отправки подарка")
        
        # 3. Отправка подарка (с логикой оплаты XTR)
        result = await send_snakebox_gift(
            client=client,
            recipient_id=recipient_telegram_id,
            recipient_hash=recipient_hash,
            gift_msg_id=final_msg_id
        )
        
        # 4. Обработка результатов
        if isinstance(result, dict) and result.get("status") == "error":
            return result
        
        if result:
            return {
                "status": "success",
                "message": "Подарок успешно отправлен",
                "data": str(result)
            }
        else:
            return {
                "status": "error",
                "error": "Неизвестная ошибка при отправке подарка, функция send_snakebox_gift вернула None."
            }
            
    except errors.RPCError as e:
        logger.exception(f"❌ Критическая RPC ошибка при отправке подарка: {e}")
        return {
            "status": "error",
            "error": f"Ошибка Telegram RPC: {e.__class__.__name__} — {e}"
        }
    except Exception as e:
        logger.exception(f"❌ Непредвиденная ошибка при отправке подарка: {e}")
        return {
            "status": "error",
            "error": str(e)
        }