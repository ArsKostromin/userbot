import os
import asyncio
import logging
from PIL import Image

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"
PLACEHOLDER_JPEG = os.path.join(MEDIA_ROOT, "placeholder.jpeg")  # путь к placeholder

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

        # --- Создаём placeholder, если его нет ---
        if not os.path.exists(PLACEHOLDER_JPEG):
            logger.info("🖼️ Placeholder не найден, создаём серый квадрат 512x512...")
            img = Image.new("RGB", (512, 512), color=(200, 200, 200))
            img.save(PLACEHOLDER_JPEG, "JPEG")

        # --- Копируем placeholder в итоговый JPEG ---
        with Image.open(PLACEHOLDER_JPEG) as img:
            img.convert("RGB").save(jpeg_path, "JPEG")

        logger.info(f"✅ JPEG готов (
