import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"


async def download_thumbnail_image(client, document, slug: str) -> str | None:
    """
    Скачивает thumbnail (превью) стикера напрямую в формате JPEG.
    """
    if not document or not slug:
        logger.warning("⚠️ Нет документа или slug, пропускаем скачивание.")
        return None

    os.makedirs(MEDIA_ROOT, exist_ok=True)
    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    try:
        # 1. Проверяем, есть ли у документа превью-картинки (thumbs)
        thumbs = getattr(document, 'thumbs', None)
        if not thumbs:
            raise ValueError("У документа нет превью (thumbs).")
            
        # 2. Выбираем лучший thumbnail (обычно последний в списке - самый большой)
        best_thumb = thumbs[-1]
        logger.info(f"📁 Скачивание превью стикера в {jpeg_path}...")

        # 3. Скачиваем медиа, передавая объект thumbnail. Telethon сам сохранит его.
        await client.download_media(best_thumb, file=jpeg_path)
        
        logger.info(f"✅ Изображение успешно скачано: {jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при скачивании thumbnail: {e}")
        # Создаем заглушку, если что-то пошло не так
        try:
            placeholder = Image.new("RGB", (512, 512), color=(200, 200, 200))
            placeholder.save(jpeg_path, "JPEG")
            logger.warning("⚠️ Используем заглушку.")
            return relative_url
        except Exception as e2:
            logger.error(f"💀 Ошибка при создании заглушки: {e2}")
            return None