import os
import asyncio
import logging
from PIL import Image
from lottie import parsers, exporters

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"


async def download_and_convert_image(client, document, slug: str) -> str | None:
    """
    Скачиваем TGS и конвертируем первый кадр в JPEG через python-lottie.
    Если что-то сломалось — делаем серый квадрат.
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

        # --- Распаковываем TGS и парсим в lottie-анимацию ---
        logger.info("🎨 Загружаем TGS в lottie-анимацию...")
        with open(tgs_path, "rb") as f:
            animation = parsers.tgs.parse_tgs(f)

        # --- Рендерим первый кадр через Pillow ---
        logger.info("🖼️ Рендерим первый кадр...")
        exporters.pillow.export_single_frame(animation, jpeg_path)

        logger.info(f"✅ JPEG готов: {jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при конвертации TGS: {e}")
        # fallback — серый квадрат
        try:
            placeholder = Image.new("RGB", (512, 512), color=(200, 200, 200))
            placeholder.save(jpeg_path, "JPEG")
            logger.warning("⚠️ Используем заглушку вместо TGS.")
            return relative_url
        except Exception as e2:
            logger.error(f"💀 Ошибка при создании заглушки: {e2}")
            return None
