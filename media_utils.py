import os
import asyncio
import logging
from PIL import Image
import rlottie_python as rlottie
import numpy as np

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"


async def download_and_convert_image(client, document, slug: str) -> str | None:
    """
    Скачиваем TGS-стикер и конвертируем первый кадр в JPEG через rlottie.
    Работает с rlottie-python==1.3.8
    """
    if not document or not slug:
        logger.warning("⚠️ Нет документа или slug, пропускаем.")
        return None

    os.makedirs(MEDIA_ROOT, exist_ok=True)

    tgs_path = os.path.join(MEDIA_ROOT, f"{slug}.tgs")
    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    try:
        logger.info(f"📁 Скачиваем TGS в {tgs_path}...")
        await client.download_media(document, file=tgs_path)

        # --- Загружаем TGS через rlottie ---
        logger.info("🎨 Загружаем TGS в rlottie...")
        animation = rlottie.load_animation(tgs_path)

        # --- Получаем первый кадр ---
        width, height = animation.size()
        width, height = width or 512, height or 512  # запасной вариант

        frame = animation.render(0, width, height)

        # --- Преобразуем ARGB -> RGBA ---
        frame_rgba = np.zeros((height, width, 4), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                pixel = frame[y * width + x]
                a = (pixel >> 24) & 0xFF
                r = (pixel >> 16) & 0xFF
                g = (pixel >> 8) & 0xFF
                b = pixel & 0xFF
                frame_rgba[y, x] = [r, g, b, a]

        img = Image.fromarray(frame_rgba, "RGBA")
        img.convert("RGB").save(jpeg_path, "JPEG")

        logger.info(f"✅ JPEG готов: {jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при конвертации TGS через rlottie: {e}")
        return None
