# core/invoice.py
import logging
import httpx # Изменено с requests на httpx для асинхронности
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


async def create_star_invoice(
    client,
    chat_id: int,
    gift_id: int,
    amount: int = 25,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Создаёт инвойс на оплату звёздами через Bot API.
    Отправляет инвойс пользователю в личные сообщения.
    
    Args:
        client: Telethon клиент (не используется, но оставлен для совместимости)
        chat_id: Telegram ID пользователя (получателя инвойса)
        gift_id: ID подарка в Django БД
        amount: Сумма в звёздах (по умолчанию 25)
        title: Заголовок инвойса
        description: Описание инвойса
    
    Returns:
        Dict с результатом создания инвойса
    """
    logger.info(f"🧾 Создание инвойса: chat_id={chat_id}, gift_id={gift_id}, amount={amount}")
    
    # Получаем токен бота из переменных окружения
    bot_token = os.getenv("STAR_TOKEN") or os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("❌ В переменных окружения отсутствует STAR_TOKEN или BOT_TOKEN")
        return {
            "ok": False,
            "error": "STAR_TOKEN или BOT_TOKEN отсутствует в переменных окружения"
        }
    
    url = f"https://api.telegram.org/bot{bot_token}/sendInvoice"
    
    payload = {
        "chat_id": chat_id,
        "title": title or "Оплата вывода NFT",
        "description": description or f"Вывод подарка #{gift_id}. Комиссия {amount} звёзд ⭐",
        "payload": f"withdraw_gift_{gift_id}",
        "provider_token": "",  # для Stars — оставить пустым!
        "currency": "XTR",
        "prices": [{"label": "Комиссия", "amount": amount}],
        "max_tip_amount": 0,
        "suggested_tip_amounts":,
    }
    
    r = None
    try:
        # Использование httpx.AsyncClient для асинхронного выполнения POST-запроса
        async with httpx.AsyncClient(timeout=20) as http_client:
            r = await http_client.post(url, json=payload)
        
        r.raise_for_status()
        data = r.json()
        
        if data.get("ok"):
            logger.info(f"✅ Инвойс успешно создан: message_id={data['result'].get('message_id')}")
            return {
                "ok": True,
                "chat_id": chat_id,
                "message_id": data["result"].get("message_id"),
                "payload": f"withdraw_gift_{gift_id}",
                "amount": amount,
                "currency": "XTR",
                "invoice_payload": f"withdraw_gift_{gift_id}"
            }
        else:
            logger.error(f"💀 Telegram API вернул ошибку: {data}")
            return {
                "ok": False,
                "error": data.get("description", "Неизвестная ошибка Telegram API")
            }
            
    except httpx.RequestError as e: # Изменено исключение на httpx
        err_data = ""
        if r is not None:
             try:
                 err_data = r.json()
             except Exception:
                 err_data = r.text
        else:
            err_data = str(e)
            
        logger.error(f"💀 Не удалось создать инвойс: {e} | Ответ: {err_data}")
        return {
            "ok": False,
            "error": str(e),
            "details": err_data
        }