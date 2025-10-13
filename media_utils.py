import os
import asyncio
import gzip
import subprocess
from PIL import Image
import logging

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"

async def download_and_convert_image(client, document, slug: str) -> str | None:
    if not document or not slug:
        logger.warning("⚠️ Нет документа или slug, пропускаем.")
        return None

    os.makedirs(MEDIA_ROOT, exist_ok=True)

    tgs_path = os.path.join(MEDIA_ROOT, f"{slug}.tgs")
    json_path = os.path.join(MEDIA_ROOT, f"{slug}.json")
    gif_path = os.path.join(MEDIA_ROOT, f"{slug}.gif")
    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    try:
        # --- Скачиваем TGS ---
        logger.info(f"📁 Скачиваем TGS в {tgs_path}...")
        await client.download_media(document, file=tgs_path)

        # --- Распаковываем в JSON ---
        with gzip.open(tgs_path, "rb") as f_in:
            with open(json_path, "wb") as f_out:
                f_out.write(f_in.read())

        # --- Конвертируем в GIF через lottie_convert (Node.js или CLI) ---
        subprocess.run([
            "lottie_convert.py", "-i", json_path, "-o", gif_path
        ], check=True)

        # --- Берем первый кадр GIF и сохраняем JPEG ---
        with Image.open(gif_path) as img:
            img.seek(0)
            img.convert("RGB").save(jpeg_path, "JPEG")

        logger.info(f"✅ JPEG готов: {jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при конвертации TGS: {e}")
        return None

    finally:
        for f in [tgs_path, gif_path, json_path]:
            if os.path.exists(f):
                os.remove(f)
