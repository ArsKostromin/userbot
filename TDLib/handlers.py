import logging

logger = logging.getLogger(__name__)

async def handle_update(update: dict):
    """Обработка апдейтов TDLib"""
    t = update.get("@type")

    if t == "updateNewMessage":
        msg = update["message"]
        chat_id = msg["chat_id"]
        content = msg["content"]
        logger.info(f"💬 Сообщение в чате {chat_id}: {content.get('@type')}")

        if content.get("@type") == "messageGiftedPremium" or "gift" in str(content).lower():
            logger.info("🎁 Обнаружен подарок!")
            # TODO: вызвать отправку в Django API
