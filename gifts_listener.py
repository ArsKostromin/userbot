from telethon import events, functions, types
import logging

logger = logging.getLogger(__name__)

def register_gift_listener(client):
    @client.on(events.NewMessage)
    async def handle_gift(event):
        action = event.message.action
        if not action:
            return

        gift_types = (
            'MessageActionGiftCode',
            'MessageActionGiftStars',
            'MessageActionGiftTon',
            'MessageActionStarGift',
            'MessageActionStarGiftUnique'
        )

        if type(action).__name__ in gift_types:
            logger.info(f"🎁 Новый подарок/NFT: {type(action).__name__}")
            logger.info(f"От кого: {getattr(action, 'from_id', 'неизвестно')}")
            logger.info(f"Содержимое: {action.to_dict()}")

            gift_id = getattr(action, 'gift', None)
            if gift_id:
                try:
                    info = await client(functions.payments.GetCollectibleInfoRequest(gift_id=gift_id))
                    logger.info(f"Метаданные NFT: {info.to_dict()}")
                except Exception as e:
                    logger.warning(f"Не удалось получить метаданные NFT: {e}")
