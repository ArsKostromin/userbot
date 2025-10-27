import logging
from telethon.tl.core import TLRequest
from telethon.tl.types import InputSavedStarGiftUser, InputPeerUser

logger = logging.getLogger(__name__)


class RawTransferStarGift(TLRequest):
    """
    Реализация TL-функции:
    payments.transferStarGift#7f18176a stargift:InputSavedStarGift to_id:InputPeer = Updates;
    """
    QUALNAME = "payments.transferStarGift"

    def __init__(self, stargift, to_id):
        self.stargift = stargift
        self.to_id = to_id


async def send_snakebox_gift(client):
    """
    Отправляет подарок "Snake Box" пользователю @jhgvcbcg (ID: 1207534564)
    через низкоуровневый RawFunction (MTProto).
    """
    try:
        logger.info("🚀 Начинаю отправку подарка 'Snake Box' пользователю @jhgvcbcg")

        # --- Конкретные данные о подарке ---
        msg_id = 41
        user_id = 1207534564
        access_hash = -8813161918532140746

        # --- Создаём объекты TL ---
        stargift = InputSavedStarGiftUser(msg_id=msg_id)
        to_peer = InputPeerUser(user_id=user_id, access_hash=access_hash)

        # --- Создаём запрос ---
        req = RawTransferStarGift(stargift=stargift, to_id=to_peer)

        # --- Отправляем его через MTProto ---
        result = await client._invoke_raw(req)

        logger.info("✅ Подарок 'Snake Box' успешно отправлен пользователю @jhgvcbcg")
        return result

    except Exception as e:
        logger.exception(f"❌ Ошибка при отправке подарка: {e}")
        raise
