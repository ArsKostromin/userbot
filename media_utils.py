import os
import asyncio
import logging
from PIL import Image

logger = logging.getLogger(__name__)
MEDIA_ROOT = "/app/media"


async def run_bash_command(cmd: str) -> bool:
    """Выполняет bash-команду и ждет её завершения."""
    # Используем shell=True для удобства, но лучше использовать list-форму.
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        logger.error(f"❌ Команда '{cmd}' завершилась с ошибкой {proc.returncode}")
        # Выводим только первые 512 символов, чтобы не загромождать лог
        logger.error(f"   STDOUT: {stdout.decode('utf-8', 'ignore')[:512]}...")
        logger.error(f"   STDERR: {stderr.decode('utf-8', 'ignore')[:512]}...")
        return False
    
    logger.info(f"✅ Команда '{cmd}' успешно выполнена.")
    return True


async def download_and_convert_image(client, document, slug: str) -> str | None:
    """
    Скачиваем TGS, конвертируем его в PNG с помощью tgs-converter (внешний инструмент),
    а затем конвертируем PNG в JPEG с помощью Pillow.
    """
    if not document or not slug:
        logger.warning("⚠️ Нет документа или slug, пропускаем.")
        return None

    os.makedirs(MEDIA_ROOT, exist_ok=True)
    tgs_path = os.path.join(MEDIA_ROOT, f"{slug}.tgs")
    temp_png_path = os.path.join(MEDIA_ROOT, f"{slug}.png")
    jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    try:
        # 1. Скачиваем TGS
        logger.info(f"📁 Скачиваем TGS в {tgs_path}...")
        await client.download_media(document, file=tgs_path)

        # 2. Конвертируем TGS в PNG с помощью tgs-converter
        logger.info(f"🎨 Конвертируем TGS в PNG через tgs-converter...")
        # tgs-converter -p (конвертировать только первый кадр)
        # -o (выходной файл)
        command = f"tgs-converter -p -o {temp_png_path} {tgs_path}"
        
        success = await run_bash_command(command)
        
        if not success or not os.path.exists(temp_png_path):
            raise Exception("Сбой при выполнении tgs-converter или файл PNG не создан.")
            
        # 3. Конвертируем PNG в JPEG с помощью Pillow
        logger.info(f"🖼️ Конвертируем PNG в JPEG с помощью Pillow...")
        
        def convert_png_to_jpeg():
            # Загружаем PNG, конвертируем в RGB (для JPEG) и сохраняем
            with Image.open(temp_png_path) as img:
                img.convert('RGB').save(jpeg_path, 'jpeg')
                
        # Pillow - синхронная библиотека, запускаем в отдельном потоке
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, convert_png_to_jpeg)

        logger.info(f"✅ JPEG готов: {jpeg_path}")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при обработке TGS: {e}")
        try:
            # Создание заглушки
            placeholder = Image.new("RGB", (512, 512), color=(200, 200, 200))
            placeholder.save(jpeg_path, "JPEG")
            logger.warning("⚠️ Используем заглушку.")
            return relative_url
        except Exception as e2:
            logger.error(f"💀 Ошибка при создании заглушки: {e2}")
            return None
    finally:
        # 4. Удаляем временные файлы
        if os.path.exists(tgs_path):
            os.remove(tgs_path)
        if os.path.exists(temp_png_path):
            os.remove(temp_png_path)