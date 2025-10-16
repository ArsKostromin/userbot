import logging
from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)
app = FastAPI()

@app.post("/test")
async def test_endpoint(request: Request):
    data = await request.json()
    logger.info(f"📩 Получен запрос от Django: {data}")
    return {"status": "ok", "message": "Запрос дошёл до userbot!"}
