# userbot/api/server.py
from fastapi import FastAPI, Request
from core.sender import send_snakebox_gift
import logging
from core.sender import send_gift_to_user
from core.telegram_client import get_client_instance

logger = logging.getLogger(__name__)
app = FastAPI()

# Глобальная переменная для хранения клиента
_client_instance = None

def set_client_instance(client):
    """Устанавливает экземпляр клиента для использования в API"""
    global _client_instance
    _client_instance = client


class SendGiftRequest(BaseModel):
    """Запрос на отправку подарка"""
    gift_id: int
    recipient_telegram_id: int
    peer_id: Optional[int] = None
    msg_id: Optional[int] = None
    access_hash: Optional[int] = None


class CreateStarInvoiceRequest(BaseModel):
    """Запрос на создание инвойса для оплаты звёздами"""
    chat_id: int
    gift_id: int
    amount: int = 25
    title: Optional[str] = None
    description: Optional[str] = None


@app.post("/send_gift")
async def send_gift(request: Request):
    data = await request.json()
    logger.info(f"📦 Запрос на передачу подарка: {data}")

    try:
        await send_real_gift(
            user_id=data.get("user_id"),
            username=data.get("username"),
            peer_id=data.get("peer_id"),
            gift_msg_id=data.get("gift_msg_id"),
            gift_name=data.get("gift_name"),
        )
        return {"status": "ok", "message": "Подарок успешно передан"}
    except Exception as e:
        logger.exception(f"❌ Ошибка при передаче подарка: {e}")
        return {"status": "error", "message": str(e)}
