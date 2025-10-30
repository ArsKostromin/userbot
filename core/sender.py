import logging
from telethon.tl import TLObject
from telethon.tl.types import InputSavedStarGiftUser, InputPeerUser
from telethon.tl.types import Updates
from telethon.helpers import pack_message

logger = logging.getLogger(__name__)


class RawTransferStarGift(TLObject):
    """
    Реализация TL-функции:
    payments.transferStarGift#7f18176a stargift:InputSavedStarGift to_id:InputPeer = Updates;
    """
    QUALNAME = "payments.transferStarGift"
    CONSTRUCTOR_ID = 0x7f18176a  # 1334171242 в десятичной форме
    SUBCLASS_OF_ID = 0x74ae4240  # Updates

    def __init__(self, stargift, to_id):
        self.stargift = stargift
        self.to_id = to_id

    def to_dict(self):
        return {
            "_": self.QUALNAME,
            "stargift": self.stargift.to_dict() if hasattr(self.stargift, "to_dict") else self.stargift,
            "to_id": self.to_id.to_dict() if hasattr(self.to_id, "to_dict") else self.to_id,
        }


async def send_snakebox_gift(client):
    """
    Отправляет подарок "Snake Box" пользователю @jhgvcbcg (ID: 1207534564)
    через низкоуровневый RawFunction (MTProto).
    """
    try:
        logger.info("🚀 Начинаю отправку подарка 'Snake Box' пользователю @jhgvcbcg")

        msg_id = 41
        user_id = 1207534564
        access_hash = -8813161918532140746

        stargift = InputSavedStarGiftUser(msg_id=msg_id)
        to_peer = InputPeerUser(user_id=user_id, access_hash=access_hash)

        req = RawTransferStarGift(stargift=stargift, to_id=to_peer)

        # используем низкоуровневый invoke
        result = await client.invoke(req)

        logger.info("✅ Подарок 'Snake Box' успешно отправлен пользователю @jhgvcbcg")
        return result

    except Exception as e:
        logger.exception(f"❌ Ошибка при отправке подарка: {e}")
        raise
