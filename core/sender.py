import logging
import asyncio
from telethon.tl.types import InputPeerUser

logger = logging.getLogger(__name__)

# 🔧 Заглушка под TDLib
async def send_gift_via_tdlib(receiver_username, gift_slug, message="🎁 Держи подарок от Snake Game!"):
    """
    Заглушка под TDLib.
    В реальности здесь будет вызов sendStarsGift через TDLib JSON.
    """
    logger.info(f"💫 [TDLib] Отправляю подарок '{gift_slug}' пользователю @{receiver_username} ...")
    await asyncio.sleep(1.2)
    logger.info(f"✅ [TDLib] Подарок '{gift_slug}' успешно передан @{receiver_username} (mock)")
    return True


# 🚀 Основная функция отправки подарка
async def send_real_gift(client, gift_data: dict):
    """
    Отправляет подарок пользователю через Telethon (или TDLib, если включено)
    gift_data: {
        "name": "Snake Box",
        "peer_id": 1207534564,
        "tg_user_name": "jhgvcbcg",
        "ton_contract_address": "SnakeBox-29826",
    }
    """
    try:
        user_id = int(gift_data.get("peer_id"))
        username = gift_data.get("tg_user_name")
        gift_name = gift_data.get("name")
        contract = gift_data.get("ton_contract_address")

        logger.info(f"🎁 Передача подарка '{gift_name}' → {username} ({user_id})")

        # Проверим подключение
        if not client.is_connected():
            await client.connect()

        # Получаем entity
        try:
            receiver = await client.get_input_entity(user_id)
        except Exception as e:
            logger.warning(f"⚠️ Не удалось получить entity по ID {user_id}: {e}, пробуем по username")
            receiver = await client.get_input_entity(username)

        # Текст сообщения о подарке
        message_text = f"🎁 Лови подарок: **{gift_name}**\n" \
                       f"🧩 Контракт: `{contract}`\n" \
                       f"💎 Отправлено из SnakeGame NFT Bot"

        # Отправка через Telethon
        sent = await client.send_message(receiver, message_text)
        logger.info(f"✅ Сообщение о подарке отправлено пользователю {username} ({user_id})")
        logger.debug(f"📤 Message ID: {sent.id}")

        # TDLib mock
        await send_gift_via_tdlib(username, contract)

    except Exception as e:
        logger.exception(f"❌ Ошибка при передаче подарка: {e}")
        raise


# 💥 Один раз при старте — передача NFT
async def send_gift_once(client):
    """
    Вызывается при запуске userbot
    Берёт данные о подарке и передаёт получателю
    """
    logger.info("🚀 Клиент инициализирован, начинаю передачу подарка...")

    gift_data = {
        "id": 5852757491946882427,
        "ton_contract_address": "SnakeBox-29826",
        "name": "Snake Box",
        "price_ton": 472.0,
        "peer_id": 1207534564,
        "tg_user_name": "jhgvcbcg",
        "sender_id": 1207534564,
        "chat_name": "[Ɐ] r",
    }

    await send_real_gift(client, gift_data)
