import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"

# 🔗 Укажи домен, на котором крутится backend
BASE_URL = "https://teststudiaorbita.ru"


async def download_thumbnail_image(client, document, slug: str) -> str | None:
    """
    Скачивает thumbnail (превью) стикера напрямую в формате JPEG.
    Возвращает абсолютный URL (например: https://teststudiaorbita.ru/media/slug.jpeg)
    """
    if not document or not slug:
        logger.warning("⚠️ Нет документа или slug, пропускаем скачивание.")
        return None

    os.makedirs(MEDIA_ROOT, exist_ok=True)
    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    image_url = f"{BASE_URL}/media/{slug}.jpeg"  # ✅ абсолютный URL для Django API

    try:
        # 1. Проверяем, есть ли превью у документа
        thumbs = getattr(document, "thumbs", None)
        if not thumbs:
            raise ValueError("У документа нет превью (thumbs).")

        # 2. Берём лучший (последний) thumbnail
        best_thumb = thumbs[-1]
        logger.info(f"📁 Скачиваем превью стикера в {jpeg_path}...")

        # 3. Скачиваем превью через Telethon
        await client.download_media(best_thumb, file=jpeg_path)

        # 4. Проверим, что файл реально создался
        if not os.path.exists(jpeg_path):
            raise FileNotFoundError("Файл превью не был создан после скачивания.")

        logger.info(f"✅ Превью успешно скачано: {jpeg_path}")
        return image_url

    except Exception as e:
        logger.error(f"❌ Ошибка при скачивании thumbnail: {e}")
        try:
            # 5. Создаём серую заглушку, если превью не получилось скачать
            placeholder = Image.new("RGB", (512, 512), color=(200, 200, 200))
            placeholder.save(jpeg_path, "JPEG")
            logger.warning("⚠️ Используем заглушку.")
            return image_url
        except Exception as e2:
            logger.error(f"💀 Ошибка при создании заглушки: {e2}")
            return None
