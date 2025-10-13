import logging
import json
import requests
# Используем импорт config, как в вашем примере
import config 
from telethon import utils

logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ БЭКЕНДА ---
# Используем константы из config
API_BASE_URL = config.API_BASE_URL
API_URL = f"{API_BASE_URL}/Inventory/adds-gift/"
AUTH_TOKEN = config.API_TOKEN

# 💡 ТОЧНЫЕ ИМЕНА АТРИБУТОВ ИЗ TELETHON, которые вы хотите извлечь
ATTRIBUTE_MAPPINGS = {
    # Ключ - это имя атрибута, которое вы хотите видеть в Django
    # Значение - это список возможных имен/типов атрибутов из StarGift
    "backdrop": ["Backdrop"],
    "model": ["Model", "Shape"],
    "pattern": ["Pattern", "Texture"],
}

def parse_attributes(attributes):
    """
    Универсальный парсер атрибутов NFT-подарка.
    Возвращает: backdrop, model, pattern и редкости (permille).
    """
    result = {
        "backdrop_name": None,
        "model_name": None,
        "pattern_name": None,
        "backdrop_rarity_permille": None,
        "model_rarity_permille": None,
        "pattern_rarity_permille": None,
        "backdrop_original_details": None,
        "model_original_details": None,
        "pattern_original_details": None,
    }

    # Для более точного парсинга, мы создаем обратную карту
    reverse_map = {}
    for django_key, tg_names in ATTRIBUTE_MAPPINGS.items():
        for tg_name in tg_names:
            reverse_map[tg_name.lower()] = django_key

    for attr in attributes or []:
        name = getattr(attr, "name", None)
        rarity = getattr(attr, "rarity_permille", None)
        orig = getattr(attr, "original_details", None)
        
        orig_details = {
            "id": getattr(orig, "id", None),
            "type": getattr(orig, "type", None),
            "name": getattr(orig, "name", None),
        } if orig else None

        # Ищем точное соответствие или подстроку
        django_key = reverse_map.get((name or "").lower())
        
        if django_key:
            result[f"{django_key}_name"] = name
            result[f"{django_key}_rarity_permille"] = rarity
            result[f"{django_key}_original_details"] = orig_details
            logger.debug(f"🎉 Атрибут '{name}' сопоставлен с полем '{django_key}'.")
        else:
            logger.debug(f"🔍 Пропущен неизвестный атрибут: {name}")

    return result


def extract_gift_data(action, message) -> dict:
    """
    Извлекает максимум возможной информации о подарке для GiftSerializer.
    """
    gift_info = getattr(action, 'gift', None)
    if not gift_info:
        logger.warning("⚠️ GiftInfo не найден в action")
        return {}

    attributes = getattr(gift_info, 'attributes', [])
    attr_data = parse_attributes(attributes)

    # 1. Основные идентификаторы и данные
    # TG ID (служит уникальным идентификатором, как ton_contract_address)
    ton_address = getattr(gift_info, 'slug', None) or str(getattr(gift_info, 'id', ''))
    title = getattr(gift_info, 'title', 'Gift')
    slug = getattr(gift_info, 'slug', None)

    # 2. Цена и редкость
    rarity_level = getattr(getattr(gift_info, 'rarity_level', None), 'name', None)
    value_amount = getattr(gift_info, 'value_amount', None)
    price_ton = value_amount / 100 if value_amount else None
    
    # 3. Изображение
    image_url = None
    
    # Поиск документа в основном сообщении (для сервисного сообщения Media в message)
    if message and getattr(message, 'media', None) and getattr(message.media, 'document', None):
        doc_id = getattr(message.media.document, 'id', None)
        if doc_id:
            image_url = f"https://t.me/sticker/{doc_id}"
            logger.debug(f"🖼 Image URL (Media Document): {image_url}")

    # Поиск документа в самом объекте подарка (чаще всего здесь)
    if not image_url and getattr(gift_info, 'document', None):
        doc = gift_info.document
        if getattr(doc, 'id', None):
            image_url = f"https://t.me/sticker/{doc.id}"
            logger.debug(f"🖼 Image URL (Gift Document): {image_url}")
            
    # Поиск по URL (если есть)
    if not image_url:
         image_url = getattr(gift_info, 'media_url', None) or getattr(gift_info, 'thumb_url', None)
         if image_url:
              logger.debug(f"🖼 Image URL (Media/Thumb URL): {image_url}")

    if not image_url:
        image_url = "https://cdn-icons-png.flaticon.com/512/3989/3989685.png"
        logger.warning("⚠️ Не удалось извлечь реальный image_url. Используется заглушка.")

    # --- Сбор итоговых данных ---
    gift_data = {
        # Данные, которые Django может использовать для поиска/создания
        "ton_contract_address": ton_address,
        "name": title,
        "symbol": slug,
        "image_url": image_url,
        "price_ton": price_ton,
        "rarity_level": rarity_level,
        
        # Визуальные атрибуты (для удобства)
        "backdrop": attr_data.get("backdrop_name"), 
        
        # Данные о редкости и деталях
        **attr_data 
    }

    # --- Логирование извлекаемых полей ---
    logger.info("--- 📊 Извлеченные поля NFT ---")
    log_data = {k: v for k, v in gift_data.items() if k not in attr_data and v is not None}
    
    # Добавляем данные отправителя/чата (они приходят в kwargs, а не из action)
    log_data.update({
         "telegram_sender_id": message.sender_id,
         "telegram_chat_id": message.chat_id,
    })
    
    logger.info(json.dumps(log_data, indent=4, ensure_ascii=False))
    logger.info("--- ----------------------- ---")


    # Убираем None и пустые значения
    return {k: v for k, v in gift_data.items() if v is not None}


async def send_to_django_backend(gift_data: dict):
    """
    Отправляет извлеченные данные подарка на Django API.
    """
    # ... (логика отправки без изменений, она выглядит правильно)

    if not API_URL:
        logger.error("❌ Переменная API_URL не установлена (проверьте config.py). Пропускаю отправку.")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {AUTH_TOKEN}' if AUTH_TOKEN else '',
    }
    
    # NOTE: Убедитесь, что 'user' и другие поля отправителя/чата добавлены в gift_data 
    # в handle_star_gift, прежде чем вызывать send_to_django_backend.
    
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
    
    # 💡 Получаем chat_entity только один раз, если нужно (уже не нужно, т.к. message.chat_id достаточно)
    chat_name = utils.get_display_name(await message.get_chat()) if message.chat_id else "Unknown Chat"

    logger.warning(f"🎁 Найден Star Gift в MSG_ID: {message.id} от {sender_name} ({sender_id}) в чате '{chat_name}'")

    # Передаем только message, так как extract_gift_data использует его напрямую
    gift_data = extract_gift_data(action, message=message)
    
    # Добавляем данные отправителя/чата, которые нужны для бэкенда (user, sender_id и т.д.)
    gift_data.update({
        "user": sender_id, # Если ваш Django использует sender_id как ID пользователя
        "telegram_sender_id": sender_id,
        "telegram_sender_name": sender_name,
        "telegram_chat_name": chat_name,
    })


    # Логирование всех данных (включая атрибуты)
    logger.info("--- 📦 Данные для GiftSerializer (JSON-формат, полные) ---")
    print(json.dumps(gift_data, indent=4, ensure_ascii=False))
    logger.info("--------------------------------------------------")

    if gift_data:
        await send_to_django_backend(gift_data)