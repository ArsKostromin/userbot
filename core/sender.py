import asyncio
import logging
from telethon import functions, types, errors

logger = logging.getLogger(__name__)


async def send_snakebox_gift(client):
    """
    Отправляет подарок "Snake Box" пользователю @jhgvcbcg (ID: 1207534564)
    через официальный метод Telethon (payments.transferStarGift).
    Совместим с telethon==1.41.2.
    """
    msg_id = 41
    user_id = 1207534564
    access_hash = -8813161918532140746

    try:
        logger.info("🚀 Начинаю отправку подарка 'Snake Box' пользователю @jhgvcbcg")

        stargift = types.InputSavedStarGiftUser(msg_id=msg_id)
        to_peer = types.InputPeerUser(user_id=user_id, access_hash=access_hash)

        result = await client(functions.payments.TransferStarGiftRequest(
            stargift=stargift,
            to_id=to_peer
        ))

        logger.info("✅ Подарок 'Snake Box' успешно отправлен пользователю @jhgvcbcg")
        return result

    # ───────────────────────────────
    #  Перехват ошибок Telethon
    # ───────────────────────────────
    except errors.FloodWaitError as e:
        logger.warning(f"⏳ Telegram просит подождать {e.seconds} сек перед повтором")
        await asyncio.sleep(e.seconds + 1)
        return await send_snakebox_gift(client)

    except errors.PaymentRequiredError:
        logger.error("💰 Недостаточно Stars или подарок недоступен для передачи.")
        logger.error("Проверь, что подарок куплен и msg_id верный.")
        return None

    except errors.UserIsBlockedError:
        logger.error("🚫 Получатель заблокировал тебя — отправка невозможна.")
        return None

    except errors.PeerIdInvalidError:
        logger.error("❌ Некорректный user_id или access_hash получателя.")
        return None

    except errors.RPCError as e:
        # Общий обработчик всех RPC ошибок
        logger.error(f"⚠️ RPC ошибка: {e.__class__.__name__} — {e}")
        return None

    except Exception as e:
        logger.exception(f"❌ Непредвиденная ошибка при отправке подарка: {e}")
        raise
