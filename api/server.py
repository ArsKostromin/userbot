# userbot/api/server.py
from fastapi import FastAPI, Request
from core.sender import send_snakebox_gift
import os
import requests
import logging

logger = logging.getLogger(__name__)
app = FastAPI()

@app.post("/send_gift")
async def send_gift(request: Request):
    data = await request.json()
    logger.info(f"📦 Запрос на передачу подарка: {data}")

    try:
        # Здесь можно вызвать send_snakebox_gift с реальными параметрами
        # Оставляем заглушку/валидатор входных данных
        return {"status": "ok", "message": "Маршрут активен"}
    except Exception as e:
        logger.exception(f"❌ Ошибка при передаче подарка: {e}")
        return {"status": "error", "message": str(e)}


@app.get("/test")
@app.post("/test")
async def test_endpoint():
    return {"ok": True, "message": "userbot API доступен"}


@app.post("/create_star_invoice")
async def create_star_invoice(request: Request):
    """
    Создаёт инвойс на оплату звёздами через Bot API.
    Ожидает JSON:
    {
      "chat_id": <telegram_id пользователя>,
      "gift_id": <int>,
      "amount": <int, по умолчанию 25>,
      "title": <str, опционально>,
      "description": <str, опционально>
    }
    Возвращает: chat_id, message_id, payload (invoice_payload), currency XTR.
    В Mini App используйте openInvoice(chat_id, message_id).
    """
    data = await request.json()
    bot_token = os.environ.get("API_TOKEN")
    if not bot_token:
        return {"ok": False, "error": "API_TOKEN не установлен в userbot"}

    chat_id = data.get("chat_id") or data.get("user_id")
    gift_id = data.get("gift_id")
    amount = int(data.get("amount", 25))
    title = data.get("title") or "Оплата вывода NFT"
    description = data.get("description") or f"Вывод подарка #{gift_id}. Комиссия {amount} ⭐"

    if not chat_id or not gift_id:
        return {"ok": False, "error": "chat_id и gift_id обязательны"}

    url = f"https://api.telegram.org/bot{bot_token}/sendInvoice"
    payload = {
        "chat_id": chat_id,
        "title": title,
        "description": description,
        "payload": f"withdraw_gift_{gift_id}",
        "provider_token": "",  # Stars
        "currency": "XTR",
        "prices": [{"label": "Комиссия", "amount": amount}],
        "max_tip_amount": 0,
        "suggested_tip_amounts": [],
    }

    try:
        resp = requests.post(url, json=payload, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        if not data.get("ok"):
            return {"ok": False, "error": data.get("description", "Ошибка Telegram API"), "raw": data}

        result = data.get("result", {})
        return {
            "ok": True,
            "chat_id": chat_id,
            "message_id": result.get("message_id"),
            "payload": result.get("invoice", {}).get("invoice_payload"),
            "currency": "XTR",
            "amount": amount,
        }
    except requests.RequestException as e:
        logger.exception(f"❌ Ошибка при создании инвойса: {e}")
        try:
            err = resp.json()
        except Exception:
            err = str(e)
        return {"ok": False, "error": str(e), "details": err}
