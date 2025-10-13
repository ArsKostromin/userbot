import os
import asyncio
import logging
from PIL import Image

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"
PLACEHOLDER_JPEG = "/app/media/placeholder.jpeg"  # заранее положи любой JPEG

async def download_and_convert_image(client, document, slug: str) -> str | None:
    """
    Скачиваем TGS, но без конвертации (lottie не используется),
    сразу кладём заглушку JPEG вместо первого кадра.
    """
    if not document or not slug:
        logger.warning("⚠️ Нет документа или slug, пропускаем.")
        return None

    os.makedirs(MEDIA_ROOT, exist_ok=True)

    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    try:
        logger.info(f"📁 Скачиваем TGS в {MEDIA_ROOT}/{slug}.tgs (но не конвертируем)...")
        await client.download_media(document, file=os.path.join(MEDIA_ROOT, f"{slug}.tgs"))

        # --- Копируем заглушку вместо реальной картинки ---
        with Image.open(PLACEHOLDER_JPEG) as img:
            img.convert("RGB").save(jpeg_path, "JPEG")

        logger.info(f"✅ JPEG готов (заглушка): {jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при работе с TGS: {e}")
        return None
