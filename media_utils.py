import os
import asyncio
import logging
import gzip
import json
import numpy as np
from PIL import Image
import rlottie_python as rlottie

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"


async def download_and_convert_image(client, document, slug: str) -> str | None:
    """
    Рабочая конвертация .tgs → .jpeg через rlottie-python==1.3.8
    Без Animation, без load_animation.
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

        # --- Распаковываем gzip ---
        logger.info("🌀 Распаковываем TGS (gzip → JSON)...")
        with gzip.open(tgs_path, "rb") as f:
            json_data = f.read().decode("utf-8")

        # --- Получаем первый кадр ---
        logger.info("🎨 Рендерим первый кадр через rlottie...")
        width, height = 512, 512
        frame = rlottie.render(json_data, 0, width, height)  # 0 = первый кадр

        # --- Преобразуем в RGBA массив ---
        frame_rgba = np.zeros((height, width, 4), dtype=np.uint8)
        for y in range(height):
            for x in range(width):
                pixel = frame[y * width + x]
                a = (pixel >> 24) & 0xFF
                r = (pixel >> 16) & 0xFF
                g = (pixel >> 8) & 0xFF
                b = pixel & 0xFF
                frame_rgba[y, x] = [r, g, b, a]

        # --- Сохраняем JPEG ---
        img = Image.fromarray(frame_rgba, "RGBA")
        img.convert("RGB").save(jpeg_path, "JPEG")

        logger.info(f"✅ JPEG готов: {jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при конвертации TGS через rlottie: {e}")
        return None
