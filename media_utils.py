import os
import logging
from PIL import Image
from telethon.tl.types import Document, PhotoSize

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"
BASE_URL = "https://teststudiaorbita.ru"

async def download_thumbnail_image(client, document: Document, slug: str) -> str | None:
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"
    full_url = f"{BASE_URL}{relative_url}"

    try:
        if not document:
            logger.warning("⚠️ Нет документа — нечего скачивать.")
            return None

        thumbs = getattr(document, "thumbs", None)
        thumb_ok = False

        # 1. Пробуем превью
        if thumbs:
            best_thumb = thumbs[-1]
            if isinstance(best_thumb, PhotoSize):
                await client.download_media(best_thumb, file=jpeg_path)
                if os.path.exists(jpeg_path) and os.path.getsize(jpeg_path) > 1000:
                    thumb_ok = True
                    logger.info(f"✅ Использовано превью из thumbs: {jpeg_path}")
        
        # 2. Если превью невалидно — качаем оригинал (.webp)
        if not thumb_ok:
            webp_path = os.path.join(MEDIA_ROOT, f"{slug}.webp")
            await client.download_media(document, file=webp_path)
            logger.info("⚙️ Конвертирую .webp → .jpeg ...")
            with Image.open(webp_path).convert("RGBA") as img:
                background = Image.new("RGBA", img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[3])
                rgb_img = background.convert("RGB")
                rgb_img.save(jpeg_path, "JPEG")

        logger.info(f"🌐 Полный URL: {full_url}")
        return full_url

    except Exception as e:
        logger.error(f"💀 Ошибка при скачивании превью: {e}")
        return None
