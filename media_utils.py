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
    Скачиваем TGS-стикер из Telegram и рендерим первый кадр в JPEG через rlottie.
    """
    if not document or not slug:
        logger.warning("⚠️ Нет документа или slug, пропускаем.")
        return None

    os.makedirs(MEDIA_ROOT, exist_ok=True)

    tgs_path = os.path.join(MEDIA_ROOT, f"{slug}.tgs")
    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    try:
        # --- Скачиваем TGS ---
        logger.info(f"📁 Скачиваем TGS в {tgs_path}...")
        await client.download_media(document, file=tgs_path)

        # --- Загружаем TGS через rlottie ---
        logger.info("🎨 Загружаем TGS в rlottie...")
        animation = rlottie.Animation.from_file(tgs_path)

        # --- Рендерим первый кадр ---
        width, height = 512, 512  # стандартный размер TGS
        frame = animation.render(0, width, height)  # индекс кадра 0

        # --- Конвертируем ARGB → RGBA для PIL ---
        frame_rgba = np.zeros((height, width, 4), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                pixel = frame[y, x]
                a = (pixel >> 24) & 0xFF
                r = (pixel >> 16) & 0xFF
                g = (pixel >> 8) & 0xFF
                b = pixel & 0xFF
                frame_rgba[y, x] = [r, g, b, a]

        # --- Сохраняем через PIL ---
        img = Image.fromarray(frame_rgba, 'RGBA')
        img.convert("RGB").save(jpeg_path, "JPEG")

        logger.info(f"✅ JPEG готов: {jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при конвертации TGS через rlottie: {e}")
        return None
