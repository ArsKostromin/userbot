import os
import logging
from telethon.tl.types import Document, PhotoSize

logger = logging.getLogger(__name__)

MEDIA_ROOT = "/app/media"
BASE_URL = "https://teststudiaorbita.ru"

async def download_thumbnail_image(client, document: Document, slug: str) -> str | None:
    """
    Скачивает превью или оригинал стикера в любом формате (webp/tgs/png/...),
    не конвертирует, просто сохраняет и пишет всё в логи.
    """
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    relative_path = None

    try:
        if not document:
            logger.warning("⚠️ Нет документа — нечего скачивать.")
            return None

        thumbs = getattr(document, "thumbs", None)
        thumb_ok = False

        # 1. Пробуем скачать превью, если оно есть
        if thumbs:
            best_thumb = thumbs[-1]
            if isinstance(best_thumb, PhotoSize):
                thumb_path = os.path.join(MEDIA_ROOT, f"{slug}_thumb")
                logger.info(f"📥 Пробую скачать превью в {thumb_path} ...")
                await client.download_media(best_thumb, file=thumb_path)
                if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 1000:
                    thumb_ok = True
                    relative_path = f"/media/{os.path.basename(thumb_path)}"
                    logger.info(f"✅ Использовано превью из thumbs: {thumb_path}")

        # 2. Если превью не найдено — качаем оригинал как есть
        if not thumb_ok:
            logger.info("⚙️ Превью нет или оно пустое — качаю оригинал...")
            orig_path = os.path.join(MEDIA_ROOT, slug)
            file_path = await client.download_media(document, file=orig_path)
            if file_path:
                relative_path = f"/media/{os.path.basename(file_path)}"
                logger.info(f"✅ Оригинал скачан: {file_path}")
            else:
                logger.error("❌ Не удалось скачать оригинал документа.")
                return None

        # 3. Возвращаем полный URL
        if relative_path:
            full_url = f"{BASE_URL}{relative_path}"
            logger.info(f"🌐 Полный URL: {full_url}")
            return full_url
        else:
            logger.error("❌ Файл не найден после скачивания.")
            return None

    except Exception as e:
        logger.error(f"💀 Ошибка при скачивании превью: {e}")
        return None
