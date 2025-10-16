# userbot/api/server.py
from fastapi import FastAPI, Request
from core.sender import send_real_gift
import logging

logger = logging.getLogger(__name__)
app = FastAPI()

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
