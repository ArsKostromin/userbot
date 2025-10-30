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
    except errors.BadRequestError as e:
        # Обрабатываем конкретные ошибки Telegram API
        if "PAYMENT_REQUIRED" in str(e):
            logger.error("❌ Недостаточно средств для отправки подарка (PAYMENT_REQUIRED)")
            logger.info("💡 Проверь баланс Stars в Telegram или купи Stars перед отправкой.")
        elif "STARGIFT_NOT_FOUND" in str(e):
            logger.error("❌ Указанный подарок (Snake Box) не найден или больше недоступен.")
        elif "PEER_ID_INVALID" in str(e):
            logger.error("❌ Неверный user_id или access_hash получателя.")
        else:
            logger.exception(f"❌ Неизвестная ошибка Telegram API: {e}")

    except Exception as e:
        logger.exception(f"❌ Критическая ошибка при отправке подарка: {e}")
        raise