# userbot/api/server.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, Union
import logging
from core.sender import send_gift_to_user
from core.telegram_client import get_client_instance

logger = logging.getLogger(__name__)
app = FastAPI(title="Userbot API", version="1.0.0")

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
    ton_contract_address: Optional[Union[str, int]] = None  # Уникальный slug подарка для поиска в инвентаре (может быть строкой или числом)
    msg_id: Optional[int] = None  # Опционально, если известен
    
    def __init__(self, **data):
        # Преобразуем ton_contract_address в строку, если он передан как число
        if 'ton_contract_address' in data and data['ton_contract_address'] is not None:
            data['ton_contract_address'] = str(data['ton_contract_address'])
        super().__init__(**data) 


class CreateStarInvoiceRequest(BaseModel):
    """Запрос на создание инвойса для оплаты звёздами"""
    chat_id: int
    gift_id: int
    amount: int = 25
    title: Optional[str] = None
    description: Optional[str] = None


@app.post("/send_gift")
async def send_gift(request: SendGiftRequest) -> Dict[str, Any]:
    """
    Асинхронный эндпоинт для отправки подарка пользователю.
    Принимает gift_id и recipient_telegram_id.
    """
    logger.info(f"📦 Запрос на отправку подарка: gift_id={request.gift_id}, recipient={request.recipient_telegram_id}, ton_contract_address={request.ton_contract_address}, msg_id={request.msg_id}")
    
    client = get_client_instance() or _client_instance
    if not client:
        logger.error("❌ Telegram клиент не инициализирован")
        raise HTTPException(status_code=503, detail="Telegram клиент не инициализирован")
    
    try:
        # Преобразуем ton_contract_address в строку, если он передан
        ton_address = None
        if request.ton_contract_address is not None:
            try:
                ton_address = str(request.ton_contract_address)
                logger.debug(f"✅ ton_contract_address преобразован в строку: {ton_address} (было: {request.ton_contract_address}, тип: {type(request.ton_contract_address).__name__})")
            except Exception as e:
                logger.error(f"❌ Ошибка при преобразовании ton_contract_address в строку: {e}, значение: {request.ton_contract_address}, тип: {type(request.ton_contract_address)}")
                raise HTTPException(status_code=400, detail=f"Некорректный формат ton_contract_address: {e}")
        
        # Вызываем send_gift_to_user, передавая необходимые параметры
        logger.debug(f"🚀 Вызов send_gift_to_user с параметрами: gift_id={request.gift_id}, recipient={request.recipient_telegram_id}, ton_address={ton_address}, msg_id={request.msg_id}")
        result = await send_gift_to_user(
            client=client,
            gift_id_external=request.gift_id, 
            recipient_telegram_id=request.recipient_telegram_id,
            ton_contract_address=ton_address,  # Для поиска в инвентаре
            gift_msg_id=request.msg_id  # Опционально, если известен
        )
        
        if result.get("status") == "success":
            return {"ok": True, "message": "Подарок успешно отправлен", "data": result}
        elif result.get("status") == "payment_required":
            return {"ok": True, "message": "Требуется оплата", "data": result}
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Неизвестная ошибка при отправке подарка")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Ошибка при отправке подарка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create_star_invoice")
async def create_star_invoice(request: CreateStarInvoiceRequest) -> Dict[str, Any]:
    """
    Асинхронный эндпоинт для создания инвойса на оплату звёздами.
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
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Ошибка создания инвойса")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Ошибка при создании инвойса: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Проверка здоровья сервиса"""
    return {
        "status": "ok",
        "client_initialized": (_client_instance is not None) or (get_client_instance() is not None)
    }