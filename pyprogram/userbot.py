import asyncio
import logging
from pyrogram import Client
from pyrogram.errors import StargiftUsageLimited
from config import API_ID, API_HASH, SESSION_PATH

# Настройка логов
logging.basicConfig(level=logging.INFO, format="pyrogram-userbot | %(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Данные о подарке и получателе
GIFT_DATA = {
    "id": 5852757491946882427,
    "ton_contract_address": "SnakeBox-29826",
    "name": "Snake Box",
    "price_ton": 472.0,
    "peer_id": 1207534564,  # id пользователя, которому отправляем
}

async def send_gift():
    async with Client(SESSION_PATH, API_ID, API_HASH) as app:
        try:
            logger.info(f"🚀 Отправка подарка {GIFT_DATA['name']} пользователю {GIFT_DATA['peer_id']}")
            await app.send_gift(
                GIFT_DATA['peer_id'],
                GIFT_DATA['id'],
                is_private=True  # true — чтобы подарок был приватным
            )
            logger.info("🎉 Подарок успешно отправлен!")
        except StargiftUsageLimited:
            logger.warning("⚠️ Лимит на отправку подарков достигнут")
        except Exception as e:
            logger.error(f"❌ Ошибка при отправке подарка: {e}")

if __name__ == "__main__":
    asyncio.run(send_gift())
