import logging
import json
import requests
import config
import os
import asyncio
from telethon import utils
# 💡 ИСПРАВЛЕНИЕ: Используем Pillow для работы с изображениями 
# и python-lottie для TGS -> GIF
from PIL import Image
from lottie.importers.tgs import import_tgs
from lottie.exporters.gif import export_gif 

logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ БЭКЕНДА И ПУТЕЙ ---
API_BASE_URL = getattr(config, 'API_BASE_URL', None)
API_URL = f"{API_BASE_URL}/Inventory/adds-gift/" if API_BASE_URL else None
AUTH_TOKEN = getattr(config, 'API_TOKEN', None)
MEDIA_ROOT = "/app/media"


async def download_and_convert_image(client, document, slug: str) -> str | None:
    """
    Скачивает TGS-стикер, конвертирует его в GIF, а затем извлекает 
    первый кадр и сохраняет его как JPEG.
    """
    if not document or not slug:
        return None

    # Убеждаемся, что папка media существует
    os.makedirs(MEDIA_ROOT, exist_ok=True)

    # Определяем пути для временных и финального файлов
    temp_tgs_path = os.path.join(MEDIA_ROOT, f"{slug}.tgs")
    temp_gif_path = os.path.join(MEDIA_ROOT, f"{slug}.gif")
    final_jpeg_path = os.path.join(MEDIA_ROOT, f"{slug}.jpeg")
    relative_url = f"/media/{slug}.jpeg"

    try:
        # 1. Скачиваем TGS файл
        logger.info(f"📁 Скачивание стикера в {temp_tgs_path}...")
        await client.download_media(document, file=temp_tgs_path)

        # 2. Конвертируем TGS в GIF с использованием python-lottie
        logger.info(f"🔄 Конвертация {temp_tgs_path} в {temp_gif_path} (временный GIF)...")
        loop = asyncio.get_running_loop()
        # Запускаем синхронные Lottie-функции в отдельном потоке
        await loop.run_in_executor(None, lambda: export_gif(import_tgs(temp_tgs_path), temp_gif_path))

        # 3. Конвертируем первый кадр GIF в JPEG с использованием Pillow
        logger.info(f"🖼️ Извлечение первого кадра GIF и сохранение в {final_jpeg_path} (JPEG)...")
        def convert_gif_to_jpeg():
            with Image.open(temp_gif_path) as img:
                img.seek(0)  # Берем первый кадр
                # Конвертируем в RGB (JPEG не поддерживает прозрачность) и сохраняем
                img.convert('RGB').save(final_jpeg_path, 'jpeg')
        
        await loop.run_in_executor(None, convert_gif_to_jpeg)
        
        logger.info(f"✅ Изображение успешно сконвертировано и сохранено.")
        return relative_url

    except Exception as e:
        logger.error(f"❌ Ошибка при скачивании или конвертации изображения: {e}")
        return None
    finally:
        # 4. Удаляем временные файлы
        if os.path.exists(temp_tgs_path):
            os.remove(temp_tgs_path)
        if os.path.exists(temp_gif_path):
            os.remove(temp_gif_path)


def extract_gift_data(action) -> dict:
    gift_info = getattr(action, 'gift', None)
    if not gift_info:
        logger.warning("⚠️ Объект 'gift' не найден в action, обработка невозможна.")
        return {}

    attributes = getattr(gift_info, 'attributes', [])
    
    model_attr = next((attr for attr in attributes if type(attr).__name__ == 'StarGiftAttributeModel'), None)
    pattern_attr = next((attr for attr in attributes if type(attr).__name__ == 'StarGiftAttributePattern'), None)
    backdrop_attr = next((attr for attr in attributes if type(attr).__name__ == 'StarGiftAttributeBackdrop'), None)

    def get_details(attr_obj):
        if not attr_obj:
            return None, None, None
        
        name = getattr(attr_obj, 'name', None)
        rarity = getattr(attr_obj, 'rarity_permille', None)
        orig = getattr(attr_obj, 'original_details', None)
        
        orig_details = {
            "id": getattr(orig, "id", None),
            "type": getattr(orig, "type", None),
            "name": getattr(orig, "name", None),
        } if orig else None
        
        return name, rarity, orig_details

    model_name, model_rarity, model_orig = get_details(model_attr)
    pattern_name, pattern_rarity, pattern_orig = get_details(pattern_attr)
    backdrop_name, backdrop_rarity, backdrop_orig = get_details(backdrop_attr)

    ton_address = getattr(gift_info, 'slug', None) or str(getattr(gift_info, 'id', ''))
    title = getattr(gift_info, 'title', 'Gift')
    slug = getattr(gift_info, 'slug', None)
    gift_id_tg = getattr(gift_info, 'id', None)
    rarity_level = getattr(getattr(gift_info, 'rarity_level', None), 'name', None)
    value_amount = getattr(gift_info, 'value_amount', None)
    price_ton = value_amount / 100 if value_amount else None

    gift_data = {
        "id": gift_id_tg,
        "ton_contract_address": ton_address,
        "name": title,
        "price_ton": price_ton,
        "backdrop": backdrop_name,
        "symbol": slug,
        "model_name": model_name,
        "pattern_name": pattern_name,
        "model_rarity_permille": model_rarity,
        "pattern_rarity_permille": pattern_rarity,
        "backdrop_rarity_permille": backdrop_rarity,
        "model_original_details": model_orig,
        "pattern_original_details": pattern_orig,
        "backdrop_original_details": backdrop_orig,
        "rarity_level": rarity_level,
        "backdrop_name": backdrop_name,
    }

    return {k: v for k, v in gift_data.items() if v is not None}


async def send_to_django_backend(gift_data: dict):
    if not API_URL:
        logger.error("❌ Переменная API_URL не установлена. Пропускаю отправку.")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {AUTH_TOKEN}' if AUTH_TOKEN else '',
    }
    
    try:
        logger.info("=== 📤 Отправка данных в Django API ===")
        response = requests.post(API_URL, json=gift_data, headers=headers, timeout=10)

        if 200 <= response.status_code < 300:
            logger.info(f"🎉 Успешно отправлено! Код ответа: {response.status_code}")
        else:
            logger.error(f"⚠️ Ошибка {response.status_code} при отправке данных в Django! Ответ: {response.text}")

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка при POST {API_URL}: {e}")


async def handle_star_gift(message, client, **kwargs):
    action = getattr(message, 'action', None)
    # 💡 ИСПРАВЛЕНИЕ: Корректный тип для Star Gift — MessageActionStarGiftUnique
    if not action or type(action).__name__ != 'MessageActionStarGiftUnique': 
        return

    sender_id = getattr(message.sender, 'id', None)
    sender_name = utils.get_display_name(message.sender)
    chat_name = utils.get_display_name(await message.get_chat()) if message.chat_id else "Unknown Chat"

    logger.warning(f"🎁 Найден Star Gift в MSG_ID: {message.id} от {sender_name} ({sender_id}) в чате '{chat_name}'")

    gift_data = extract_gift_data(action)
    
    # Скачиваем и конвертируем изображение
    gift_info = getattr(action, 'gift', None)
    image_url = None
    if gift_info:
        model_attr = next((attr for attr in getattr(gift_info, 'attributes', []) if type(attr).__name__ == 'StarGiftAttributeModel'), None)
        document = getattr(model_attr, 'document', None)
        slug = gift_data.get('symbol')
        
        if document and slug:
            image_url = await download_and_convert_image(client, document, slug)
    
    # Обновляем URL или используем заглушку
    gift_data['image_url'] = image_url or "https://teststudiaorbita.ru/media/avatars/diamond.jpg"
    if not image_url:
        logger.warning("⚠️ Не удалось создать локальное изображение. Используется заглушка.")

    gift_data.update({"user": sender_id})

    logger.info("--- 📦 Данные для GiftSerializer (JSON-формат, полные) ---")
    logger.info(json.dumps(gift_data, indent=4, ensure_ascii=False))
    logger.info("--------------------------------------------------")

    if gift_data:
        await send_to_django_backend(gift_data)