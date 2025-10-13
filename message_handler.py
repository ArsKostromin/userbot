import logging
import json
import requests
import config
from telethon import utils

logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ БЭКЕНДА ---
API_BASE_URL = getattr(config, 'API_BASE_URL', None)
API_URL = f"{API_BASE_URL}/Inventory/adds-gift/" if API_BASE_URL else None
AUTH_TOKEN = getattr(config, 'API_TOKEN', None)


def extract_gift_data(action, message) -> dict:
    """
    Извлекает максимум информации о подарке, определяя атрибуты по их типу.
    """
    gift_info = getattr(action, 'gift', None)
    if not gift_info:
        logger.warning("⚠️ Объект 'gift' не найден в action, обработка невозможна.")
        return {}

    # --- 1. Извлечение атрибутов (Model, Pattern, Backdrop) по типу объекта ---
    attributes = getattr(gift_info, 'attributes', [])
    
    model_attr = next((attr for attr in attributes if type(attr).__name__ == 'StarGiftAttributeModel'), None)
    pattern_attr = next((attr for attr in attributes if type(attr).__name__ == 'StarGiftAttributePattern'), None)
    backdrop_attr = next((attr for attr in attributes if type(attr).__name__ == 'StarGiftAttributeBackdrop'), None)

    def get_details(attr_obj):
        """Вспомогательная функция для извлечения деталей из атрибута."""
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

    # --- 2. Извлечение основной информации о подарке ---
    ton_address = getattr(gift_info, 'slug', None) or str(getattr(gift_info, 'id', ''))
    title = getattr(gift_info, 'title', 'Gift')
    slug = getattr(gift_info, 'slug', None)
    
    # ID самого объекта подарка
    gift_id_tg = getattr(gift_info, 'id', None)
    
    # Цена и общая редкость
    rarity_level = getattr(getattr(gift_info, 'rarity_level', None), 'name', None)
    value_amount = getattr(gift_info, 'value_amount', None)
    price_ton = value_amount / 100 if value_amount else None

    # --- 3. Правильное извлечение Image URL ---
    image_url = None
    # Изображение чаще всего находится в документе атрибута Модели
    if model_attr and getattr(model_attr, 'document', None):
        doc_id = getattr(model_attr.document, 'id', None)
        if doc_id:
            image_url = f"https://t.me/sticker/{doc_id}"
            logger.debug(f"🖼 Image URL извлечен из атрибута Модели: {image_url}")
    
    if not image_url:
        image_url = "https://cdn-icons-png.flaticon.com/512/3989/3989685.png"
        logger.warning("⚠️ Не удалось извлечь реальный image_url. Используется заглушка.")

    # --- 4. Сборка финального словаря ---
    gift_data = {
        "id": gift_id_tg,
        "ton_contract_address": ton_address,
        "name": title,
        "image_url": image_url,
        "price_ton": price_ton,
        "backdrop": backdrop_name, # <-- Это поле дублирует backdrop_name, но оставляю, так как оно в вашем списке
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

    # Возвращаем словарь, очищенный от пустых значений
    return {k: v for k, v in gift_data.items() if v is not None}


async def send_to_django_backend(gift_data: dict):
    """
    Отправляет извлеченные данные подарка на Django API.
    """
    if not API_URL:
        logger.error("❌ Переменная API_URL не установлена (проверьте config.py). Пропускаю отправку.")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {AUTH_TOKEN}' if AUTH_TOKEN else '',
    }
    
    try:
        logger.info("=== 📤 Отправка данных в Django API ===")
        logger.info(f"URL: {API_URL}")
        logger.debug(f"Тело запроса:\n{json.dumps(gift_data, indent=4, ensure_ascii=False)}")
        
        response = requests.post(API_URL, json=gift_data, headers=headers, timeout=10)

        if 200 <= response.status_code < 300:
            logger.info(f"🎉 Успешно отправлено! Код ответа: {response.status_code}")
            logger.debug(f"Ответ Django:\n{response.text}")
        else:
            logger.error(f"⚠️ Ошибка {response.status_code} при отправке данных в Django!")
            logger.error(f"Ответ сервера:\n{response.text}")

        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка при POST {API_URL}: {e}")
        logger.debug(f"Неотправленные данные:\n{json.dumps(gift_data, indent=4, ensure_ascii=False)}")


async def handle_star_gift(message, client, **kwargs):
    """
    Основной обработчик для MessageActionStarGiftUnique.
    """
    action = getattr(message, 'action', None)
    if not action or type(action).__name__ != 'MessageActionStarGiftUnique':
        return

    sender_id = getattr(message.sender, 'id', None)
    sender_name = utils.get_display_name(message.sender)
    chat_name = utils.get_display_name(await message.get_chat()) if message.chat_id else "Unknown Chat"

    logger.warning(f"🎁 Найден Star Gift в MSG_ID: {message.id} от {sender_name} ({sender_id}) в чате '{chat_name}'")

    # 1. Извлекаем все данные о подарке
    gift_data = extract_gift_data(action, message=message)
    
    # 2. Добавляем данные отправителя/чата в общий словарь
    gift_data.update({
        "user": sender_id, # Соответствует полю "user" в вашем списке
    })

    # 3. Логирование всех данных, которые будут отправлены
    logger.info("--- 📦 Данные для GiftSerializer (JSON-формат, полные) ---")
    logger.info(json.dumps(gift_data, indent=4, ensure_ascii=False))
    logger.info("--------------------------------------------------")

    if gift_data:
        await send_to_django_backend(gift_data)
        