# userbot/core/sender.py
import logging
from telethon import TelegramClient
from telethon.tl.types import (
    InputPeerUser,
    InputSavedStarGiftUser,
)
from telethon.tl.functions.payments import TransferStarGift

logger = logging.getLogger(__name__)

API_ID = 123456   # твой api_id
API_HASH = "your_api_hash"
SESSION = "userbot"

RECIPIENT_ID = 1207534564
RECIPIENT_ACCESS_HASH = -8813161918532140746
GIFT_MESSAGE_ID = 41

async def send_collectible_gift():
    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()

    try:
        logger.info("🚀 Начинаем передачу коллекционного подарка через MTProto...")

        # Формируем InputPeerUser — получатель
        peer = InputPeerUser(user_id=RECIPIENT_ID, access_hash=RECIPIENT_ACCESS_HASH)

        # Указываем, какой подарок передаём (по message_id)
        stargift = InputSavedStarGiftUser(msg_id=GIFT_MESSAGE_ID)

        # Вызов MTProto метода напрямую
        result = await client.invoke(
            TransferStarGift(
                stargift=stargift,
                to_id=peer
            )
        )

        logger.info("✅ Коллекционный подарок успешно передан!")
        logger.info(f"Ответ от Telegram: {result}")

    except Exception as e:
        logger.exception(f"❌ Ошибка при передаче подарка: {e}")
    finally:
        await client.disconnect()
