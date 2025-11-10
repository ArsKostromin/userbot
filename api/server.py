# userbot/api/server.py
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
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
async def send_gift(request: SendGiftRequest):
    """
    Эндпоинт для отправки подарка пользователю.
    Принимает gift_id и recipient_telegram_id.
    """
    logger.info(f"📦 Запрос на отправку подарка: gift_id={request.gift_id}, recipient={request.recipient_telegram_id}")
    
    client = get_client_instance() or _client_instance
    if not client:
        raise HTTPException(status_code=503, detail="Telegram клиент не инициализирован")
    
    try:
        result = await send_gift_to_user(
            client=client,
            gift_id=request.gift_id,
            recipient_telegram_id=request.recipient_telegram_id,
            peer_id=request.peer_id,
            msg_id=request.msg_id,
            access_hash=request.access_hash
        )
        
        if result.get("status") == "success":
            return {"ok": True, "message": "Подарок успешно отправлен", "data": result}
        else:
            return {"ok": False, "error": result.get("error", "Неизвестная ошибка"), "data": result}
            
    except Exception as e:
        logger.exception(f"❌ Ошибка при отправке подарка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create_star_invoice")
async def create_star_invoice(request: CreateStarInvoiceRequest):
    """
    Эндпоинт для создания инвойса на оплату звёздами.
    Используется Django для создания инвойса при запросе на вывод подарка.
    """
    logger.info(f"🧾 Запрос на создание инвойса: chat_id={request.chat_id}, gift_id={request.gift_id}, amount={request.amount}")
    
    client = get_client_instance() or _client_instance
    if not client:
        raise HTTPException(status_code=503, detail="Telegram клиент не инициализирован")
    
    try:
        from core.invoice import create_star_invoice
        
        result = await create_star_invoice(
            client=client,
            chat_id=request.chat_id,
            gift_id=request.gift_id,
            amount=request.amount,
            title=request.title or "Оплата вывода NFT",
            description=request.description or f"Вывод подарка #{request.gift_id}. Комиссия {request.amount}⭐"
        )
        
        if result.get("ok"):
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Ошибка создания инвойса"))
            
    except Exception as e:
        logger.exception(f"❌ Ошибка при создании инвойса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "ok",
        "client_initialized": (_client_instance is not None) or (get_client_instance() is not None)
    }
