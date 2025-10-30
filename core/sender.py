import logging
from telethon import functions, types

logger = logging.getLogger(__name__)


async def send_gift_once(client):
    """
    Отправляет подарок "Snake Box" пользователю @jhgvcbcg (ID: 1207534564)
    через официальный метод Telethon:
    payments.transferStarGift#7f18176a stargift:InputSavedStarGift to_id:InputPeer = Updates;
    """
    try:
        logger.info("🚀 Начинаю отправку подарка 'Snake Box' пользователю @jhgvcbcg")

        # --- Конкретные данные о подарке и пользователе ---
        msg_id = 41
        user_id = 1207534564
        access_hash = -8813161918532140746

        # --- Создаём объекты TL ---
        stargift = types.InputSavedStarGiftUser(msg_id=msg_id)
        to_peer = types.InputPeerUser(user_id=user_id, access_hash=access_hash)

        # --- Отправляем запрос Telethon ---
        result = await client(functions.payments.TransferStarGiftRequest(
            stargift=stargift,
            to_id=to_peer
        ))

        logger.info("✅ Подарок 'Snake Box' успешно отправлен пользователю @jhgvcbcg")
        return result

    except Exception as e:
        logger.exception(f"❌ Ошибка при отправке подарка: {e}")
        raise
