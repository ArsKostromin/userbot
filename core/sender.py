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


async def find_gift_msg_id_by_ton_address(client, ton_contract_address: Optional[str]) -> Optional[int]:
    """
    Ищет msg_id подарка в инвентаре Userbot по ton_contract_address (slug).
    Это работает даже если подарок был выигран, а не получен через сообщение.
    
    Args:
        client: Telethon клиент
        ton_contract_address: Уникальный идентификатор подарка (slug) из Django БД
    
    Returns:
        msg_id подарка из инвентаря или None
    """
    if not ton_contract_address:
        logger.warning("❌ ton_contract_address не передан")
        return None
    
    # Преобразуем в строку для сравнения
    try:
        ton_contract_address_str = str(ton_contract_address)
        logger.info(f"🔎 Поиск подарка по ton_contract_address={ton_contract_address_str} (тип: {type(ton_contract_address).__name__}) в инвентаре userbot...")
    except Exception as e:
        logger.error(f"❌ Ошибка при преобразовании ton_contract_address в строку: {e}, значение: {ton_contract_address}, тип: {type(ton_contract_address)}")
        return None
    
    try:
        # GetSavedStarGiftsRequest требует peer - используем InputPeerSelf для личных сообщений
        peer = types.InputPeerSelf()
        logger.debug(f"📋 Запрос инвентаря подарков через GetSavedStarGiftsRequest...")
        
        inventory_result = await client(functions.payments.GetSavedStarGiftsRequest(
            peer=peer,
            offset=0,
            limit=1000 
        ))
        
        logger.info(f"📦 Получено подарков в инвентаре: {len(inventory_result.gifts)}")
        
        checked_count = 0
        for gift_struct in inventory_result.gifts:
            checked_count += 1
            try:
                # gift_struct - это SavedStarGiftUser или SavedStarGiftChat
                if not hasattr(gift_struct, 'gift'):
                    logger.debug(f"⚠️ Подарок #{checked_count} не имеет атрибута 'gift', пропускаем")
                    continue
                    
                if not hasattr(gift_struct, 'msg_id'):
                    logger.debug(f"⚠️ Подарок #{checked_count} не имеет атрибута 'msg_id', пропускаем")
                    continue
                
                gift_info = gift_struct.gift
                msg_id = gift_struct.msg_id
                
                # Получаем slug из подарка (соответствует ton_contract_address)
                gift_slug = getattr(gift_info, 'slug', None)
                
                if gift_slug is None:
                    logger.debug(f"⚠️ Подарок msg_id={msg_id} не имеет slug, пропускаем")
                    continue
                
                # Преобразуем slug в строку и сравниваем
                try:
                    gift_slug_str = str(gift_slug)
                    logger.debug(f"🔍 Проверка подарка msg_id={msg_id}: slug={gift_slug_str} (тип: {type(gift_slug).__name__}) vs искомый={ton_contract_address_str}")
                    
                    if gift_slug_str == ton_contract_address_str:
                        logger.info(f"✅ Найден подарок: msg_id={msg_id}, slug={gift_slug_str}")
                        return msg_id
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка при преобразовании slug в строку для msg_id={msg_id}: {e}, slug={gift_slug}, тип={type(gift_slug)}")
                    continue
                    
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при обработке подарка #{checked_count}: {e}")
                continue

        logger.warning(f"❌ Подарок с ton_contract_address={ton_contract_address_str} не найден в инвентаре (проверено {checked_count} подарков).")
        return None

    except errors.RPCError as e:
        logger.error(f"❌ Ошибка RPC при получении инвентаря: {e.__class__.__name__} — {e}")
        return None
    except Exception as e:
        logger.exception(f"❌ Критическая ошибка при поиске подарка: {e}, тип ошибки: {type(e).__name__}")
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
    ton_contract_address: Optional[str] = None,
    gift_msg_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Отправляет подарок пользователю.
    Ищет подарок в инвентаре по ton_contract_address (slug), что работает даже для выигранных подарков.
    
    Args:
        client: Telethon клиент (Userbot)
        gift_id_external: ID подарка из Django БД (для логирования)
        recipient_telegram_id: Telegram ID получателя
        ton_contract_address: Уникальный slug подарка (используется для поиска в инвентаре)
        gift_msg_id: ID сообщения с подарком (если известен, используется напрямую)
    
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
            if ton_contract_address:
                logger.info(f"🔍 msg_id не передан, ищем подарок в инвентаре по ton_contract_address={ton_contract_address}")
                # Если msg_id не передан, ищем подарок в инвентаре по ton_contract_address (slug)
                final_msg_id = await find_gift_msg_id_by_ton_address(client, ton_contract_address)
            else:
                logger.error(f"❌ Не указаны ни msg_id, ни ton_contract_address для поиска подарка")
                return {
                    "status": "error",
                    "error": "Не указаны параметры для поиска подарка (msg_id или ton_contract_address)"
                }
        
        if not final_msg_id:
            logger.error(f"❌ Не удалось найти подарок в инвентаре userbot")
            return {
                "status": "error",
                "error": f"Не удалось найти подарок в инвентаре userbot. Убедитесь, что подарок с ton_contract_address={ton_contract_address} есть в инвентаре."
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