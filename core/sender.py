import asyncio
import logging
from telethon.tl.functions.messages import SendMediaRequest
from telethon.tl.types import InputPeerUser, InputMediaPhotoExternal, InputMessageEntityTextUrl

logger = logging.getLogger(__name__)

async def send_gift_once(client):
    """
    Отправляет один подарок пользователю jhgvcbcg.
    """
    try:
        # --- данные о пользователе ---
        user_id = 1207534564
        access_hash = -8813161918532140746
        username = "jhgvcbcg"

        # --- данные о подарке ---
        gift_data = {
            "id": 5852757491946882427,
            "name": "Snake Box",
            "symbol": "SnakeBox-29826",
            "price_ton": 472.0,
            "image_url": "https://nft.fragment.com/gift/SnakeBox-29826.medium.jpg",
            "description": "NFT подарок Snake Box (модель Purple, узор Spades, фон Azure Blue)"
        }

        # --- создаём peer ---
        peer = InputPeerUser(user_id=user_id, access_hash=access_hash)

        # --- создаём медиа объект (из внешнего URL картинки) ---
        media = InputMediaPhotoExternal(
            url=gift_data["image_url"]
        )

        # --- текст сообщения ---
        message_text = (
            f"🎁 Тебе подарок, @{username}!\n\n"
            f"{gift_data['name']} ({gift_data['symbol']})\n"
            f"💎 {gift_data['price_ton']} TON\n\n"
            f"{gift_data['description']}"
        )

        # --- добавляем кликабельную ссылку на NFT ---
        entities = [
            InputMessageEntityTextUrl(
                offset=0,
                length=2,  # для ссылки типа [🎁]
                url=f"https://fragment.com/nft/{gift_data['symbol']}"
            )
        ]

        # --- отправляем ---
        await client(SendMediaRequest(
            peer=peer,
            media=media,
            message=message_text,
            entities=entities,
            random_id=client.rnd_id()
        ))

        logger.info(f"✅ Успешно отправлен подарок пользователю @{username} ({user_id})")

    except Exception as e:
        logger.exception(f"❌ Ошибка при отправке подарка: {e}")
