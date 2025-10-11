from telethon import events, functions
import logging
from message_handler import handle_star_gift

logger = logging.getLogger(__name__)

def register_gift_listener(client):
    """
    Подписка на все новые сообщения, чтобы ловить подарки/NFT
    """
    @client.on(events.NewMessage)
    async def handle_gift(event):
        message = event.message
        action = getattr(message, 'action', None)
        if not action:
            return

        # Типы подарков/NFT
        gift_types = (
            'MessageActionGiftCode',
            'MessageActionGiftStars',
            'MessageActionGiftTon',
            'MessageActionStarGift',
            'MessageActionStarGiftUnique'
        )

        action_type = type(action).__name__
        if action_type in gift_types:
            logger.info(f"🎁 Новый подарок/NFT: {action_type} в чате {message.chat_id}")

            try:
                # Вызываем уже готовый обработчик из message_handler
                await handle_star_gift(message, client,
                                       chat_name=getattr(message.chat, 'title', None),
                                       chat_username=getattr(message.chat, 'username', None),
                                       sender_info=None)
            except Exception as e:
                logger.error(f"⚠️ Ошибка при обработке подарка/NFT: {e}")
