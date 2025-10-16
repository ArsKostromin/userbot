# userbot/core/sender.py
import logging
from telethon import functions, types
from .telegram_client import get_client

logger = logging.getLogger(__name__)

async def send_real_gift(user_id: int, username: str, peer_id, gift_msg_id: int, gift_name: str = None):
    client = get_client()
    if not client:
        raise RuntimeError("❌ Клиент Telegram не инициализирован")

    receiver = user_id or f"@{username}"
    gift_name = gift_name or "Неизвестный подарок"

    logger.info(f"🎁 Передача подарка '{gift_name}' → {receiver}")

    try:
        # Подгружаем inline-кнопки из сообщения с подарком
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

        # Отправляем callback-запрос на кнопку "Передать"
        await client(
            functions.messages.GetBotCallbackAnswerRequest(
                peer=peer_id,
                msg_id=gift_msg_id,
                data=transfer_button.data
            )
        )

        logger.info(f"✅ Подарок '{gift_name}' успешно передан пользователю {receiver}")

    except Exception as e:
        logger.exception(f"❌ Ошибка при передаче подарка: {e}")
        raise
