import asyncio
import logging
from TDLib.td_client import TDLibClient
from TDLib.handlers import handle_update

logger = logging.getLogger(__name__)

async def run_tdlib():
    client = TDLibClient()
    await client.authorize()

    logger.info("📡 Начинаем слушать апдейты...")
    while True:
        update = client.receive()
        if update:
            await handle_update(update)
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    try:
        asyncio.run(run_tdlib())
    except KeyboardInterrupt:
        logger.info("🛑 TDLib клиент остановлен пользователем.")
