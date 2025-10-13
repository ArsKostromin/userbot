import os
import asyncio
import logging
from PIL import Image
from lottie import importers
from lottie.exporters import exporters

logger = logging.getLogger(__name__)

MEDIA_ROOT = "/app/media"

async def download_and_convert_image(client, document, slug: str) -> str | None:
    """
    Скачивает TGS-стикер из Telegram, конвертирует его в GIF через lottie,
    затем берёт первый кадр GIF и сохраняет как JPEG.
    
    Возвращает относительный путь к JPEG или None при ошибке.
    """
    if not document or not slug:
        logger.warning("⚠️ Нет документа или slug, пропускаем.")
        return None

    os.makedirs(MEDIA_ROOT, exist_ok=True)

    tgs_path = os.path.join(MEDIA_ROOT, f"{slug}.tgs")
    gif_path = os.path.join(MEDIA_ROOT, f"{slug}.gif")
    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    try:
        # --- Скачиваем TGS ---
        logger.info(f"📁 Скачиваем TGS в {tgs_path}...")
        await client.download_media(document, file=tgs_path)

        loop = asyncio.get_running_loop()

        # --- Конвертируем TGS → GIF ---
        async def tgs_to_gif():
            def _convert():
                anim = importers.tgs.import_tgs(tgs_path)
                exporters.gif.export_gif(anim, gif_path)
            await loop.run_in_executor(None, _convert)
        
        await tgs_to_gif()

        # --- Берем первый кадр GIF и сохраняем как JPEG ---
        async def gif_to_jpeg():
            def _extract():
                with Image.open(gif_path) as img:
                    img.seek(0)
                    img.convert("RGB").save(jpeg_path, "JPEG")
            await loop.run_in_executor(None, _extract)
        
        await gif_to_jpeg()

        logger.info(f"✅ JPEG готов: {jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при конвертации TGS: {e}")
        return None

    finally:
        # --- Чистим временные файлы ---
        for f in [tgs_path, gif_path]:
            if os.path.exists(f):
                os.remove(f)
