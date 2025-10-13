import os
import asyncio
import logging
from PIL import Image
from lottie import importers
from lottie.exporters import exporters

logger = logging.getLogger(__name__)

# Папка для медиа-файлов
MEDIA_ROOT = "/app/media"

async def download_and_convert_image(client, document, slug: str) -> str | None:
    """
    Скачивает TGS-стикер из Telegram, конвертирует его в GIF через lottie,
    затем берёт первый кадр GIF и сохраняет как JPEG.
    
    Возвращает относительный путь к JPEG или None при ошибке.
    """
    if not document or not slug:
        logger.warning("⚠️ Нет документа или slug, пропускаем конвертацию.")
        return None

    os.makedirs(MEDIA_ROOT, exist_ok=True)

    temp_tgs_path = os.path.join(MEDIA_ROOT, f"{slug}.tgs")
    temp_gif_path = os.path.join(MEDIA_ROOT, f"{slug}.gif")
    final_jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    try:
        # --- Шаг 1: Скачиваем TGS ---
        logger.info(f"📁 Скачивание стикера в {temp_tgs_path}...")
        await client.download_media(document, file=temp_tgs_path)

        loop = asyncio.get_running_loop()

        # --- Шаг 2: Конвертируем TGS → GIF ---
        def convert_tgs_to_gif():
            logger.info(f"🔄 Конвертация {temp_tgs_path} в GIF {temp_gif_path}...")
            anim = importers.tgs.import_tgs(temp_tgs_path)  # импортируем TGS как анимацию
            exporters.gif.export_gif(anim, temp_gif_path)   # сохраняем GIF

        await loop.run_in_executor(None, convert_tgs_to_gif)

        # --- Шаг 3: Берём первый кадр GIF и сохраняем как JPEG ---
        def gif_to_jpeg():
            logger.info(f"🖼️ Извлечение первого кадра GIF и сохранение в {final_jpeg_path}...")
            with Image.open(temp_gif_path) as img:
                img.seek(0)  # первый кадр
                img.convert("RGB").save(final_jpeg_path, "JPEG")  # JPEG не поддерживает прозрачность

        await loop.run_in_executor(None, gif_to_jpeg)

        logger.info(f"✅ Изображение успешно сохранено в {final_jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при скачивании или конвертации изображения: {e}")
        return None

    finally:
        # --- Удаляем временные файлы ---
        for f in [temp_tgs_path, temp_gif_path]:
            if os.path.exists(f):
                os.remove(f)
