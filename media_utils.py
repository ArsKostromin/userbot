import os
import logging
from telethon.tl.types import Document, PhotoSize

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"

async def download_thumbnail_image(client, document: Document, slug: str) -> str | None:
    """
    Скачивает thumbnail (превью) стикера напрямую в формате JPEG.
    Просто скачивает и пишет всё в логи, без заглушек и приколов.
    """
    os.makedirs(MEDIA_ROOT, exist_ok=True)
    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    try:
        if not document:
            logger.warning("⚠️ Нет документа — нечего скачивать.")
            return None

        # 1. Проверяем, есть ли превью
        thumbs = getattr(document, "thumbs", None)
        if not thumbs:
            logger.warning("❌ У документа нет превью (thumbs).")
            return None

        # 2. Выбираем лучшее превью
        best_thumb = thumbs[-1]
        if not isinstance(best_thumb, PhotoSize):
            logger.warning("❌ Неизвестный тип превью.")
            return None

        # 3. Качаем
        logger.info(f"📥 Скачиваю thumbnail в {jpeg_path} ...")
        await client.download_media(best_thumb, file=jpeg_path)

        # 4. Проверяем, что файл реально появился
        if not os.path.exists(jpeg_path):
            logger.error("❌ Файл превью не был создан после скачивания.")
            return None

        # 5. Пишем успех
        logger.info(f"✅ Превью успешно скачано: {jpeg_path}")
        logger.info(f"🌐 URL: {relative_url}")
        return relative_url

    except Exception as e:
        logger.error(f"💀 Ошибка при скачивании превью: {e}")
        return None
