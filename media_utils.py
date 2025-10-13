import os
import asyncio
import logging
from PIL import Image

# 💡 ИСПРАВЛЕНИЕ 1: Правильные пути импорта для python-lottie (v0.7.1)
# Функции импорта находятся в lottie.parsers, а не в lottie.importers
from lottie.parsers.tgs import parse_tgs 
# Функции экспорта находятся в lottie.exporters.pillow
from lottie.exporters.pillow import export_single_frame

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"


async def download_and_convert_image(client, document, slug: str) -> str | None:
    """
    Скачиваем TGS и конвертируем первый кадр в JPEG через python-lottie (MattBas).
    """
    if not document or not slug:
        logger.warning("⚠️ Нет документа или slug, пропускаем.")
        return None

    os.makedirs(MEDIA_ROOT, exist_ok=True)
    tgs_path = os.path.join(MEDIA_ROOT, f"{slug}.tgs")
    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    # Создаем объект Loop для использования run_in_executor
    loop = asyncio.get_running_loop() 

    try:
        # --- Скачиваем TGS ---
        logger.info(f"📁 Скачиваем TGS в {tgs_path}...")
        await client.download_media(document, file=tgs_path)

        # --- Загружаем TGS-анимацию ---
        logger.info("🎨 Загружаем TGS в lottie-анимацию...")
        
        # Lottie-функции синхронны, запускаем их в executor
        def load_and_parse():
            with open(tgs_path, "rb") as f:
                # 💡 ИСПРАВЛЕНИЕ 2: Используем parse_tgs для парсинга содержимого файла. 
                # load_tgs не является функцией в lottie.parsers.tgs
                return parse_tgs(f.read())
        
        animation = await loop.run_in_executor(None, load_and_parse)

        # --- Рендерим первый кадр ---
        logger.info("🖼️ Рендерим первый кадр...")
        
        # 💡 ИСПРАВЛЕНИЕ 3 (Логическое): Export Pillow требует пути к файлу
        # и объекта Animation.
        await loop.run_in_executor(None, export_single_frame, animation, jpeg_path)

        logger.info(f"✅ JPEG готов: {jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при конвертации TGS: {e}")
        try:
            # Используем Pillow для создания заглушки (она асинхронности не требует)
            placeholder = Image.new("RGB", (512, 512), color=(200, 200, 200))
            placeholder.save(jpeg_path, "JPEG")
            logger.warning("⚠️ Используем заглушку.")
            return relative_url
        except Exception as e2:
            logger.error(f"💀 Ошибка при создании заглушки: {e2}")
            return None
    finally:
        # 4. Удаляем временный TGS файл
        if os.path.exists(tgs_path):
            os.remove(tgs_path)