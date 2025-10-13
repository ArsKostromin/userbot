import logging
import json
import requests
import config
from telethon import utils

logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ БЭКЕНДА ---
API_BASE_URL = config.API_BASE_URL
API_URL = f"{API_BASE_URL}/Inventory/adds-gift/"
AUTH_TOKEN = config.API_TOKEN


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

    for attr in attributes or []:
        name = getattr(attr, "name", None)
        rarity = getattr(attr, "rarity_permille", None)
        orig = getattr(attr, "original_details", None)
        orig_details = {
            "id": getattr(orig, "id", None),
            "type": getattr(orig, "type", None),
            "name": getattr(orig, "name", None),
        } if orig else None

        # Логика классификации атрибутов
        lname = (name or "").lower()
        if "backdrop" in lname or "background" in lname or "bg" in lname:
            result["backdrop_name"] = name
            result["backdrop_rarity_permille"] = rarity
            result["backdrop_original_details"] = orig_details
        elif "model" in lname or "body" in lname or "shape" in lname:
            result["model_name"] = name
            result["model_rarity_permille"] = rarity
            result["model_original_details"] = orig_details
        elif "pattern" in lname or "texture" in lname or "stripe" in lname or "design" in lname:
            result["pattern_name"] = name
            result["pattern_rarity_permille"] = rarity
            result["pattern_original_details"] = orig_details

    return result


def extract_gift_data(action, sender_id=None, sender_name=None, chat_name=None, message=None) -> dict:
    """
    Извлекает максимум возможной информации о подарке для GiftSerializer.
    """
    gift_info = getattr(action, 'gift', None)
    if not gift_info:
        logger.warning("⚠️ GiftInfo не найден в action")
        return {}

    attributes = getattr(gift_info, 'attributes', [])
    attr_data = parse_attributes(attributes)

    ton_address = getattr(gift_info, 'slug', None) or str(getattr(gift_info, 'id', ''))
    slug = getattr(gift_info, 'slug', None)
    title = getattr(gift_info, 'title', 'Gift')

    # 🖼 Изображение
    image_url = None
    if message and getattr(message, 'media', None) and getattr(message.media, 'document', None):
        doc_id = getattr(message.media.document, 'id', None)
        if doc_id:
            image_url = f"https://t.me/sticker/{doc_id}"
    elif getattr(gift_info, 'document', None):
        doc = gift_info.document
        if getattr(doc, 'id', None):
            image_url = f"https://t.me/sticker/{doc.id}"
    elif getattr(gift_info, 'media_url', None):
        image_url = getattr(gift_info, 'media_url')
    elif getattr(gift_info, 'thumb_url', None):
        image_url = getattr(gift_info, 'thumb_url')

    if not image_url:
        image_url = "https://cdn-icons-png.flaticon.com/512/3989/3989685.png"

    rarity_level = getattr(getattr(gift_info, 'rarity_level', None), 'name', None)
    value_amount = getattr(gift_info, 'value_amount', None)
    price_ton = value_amount / 100 if value_amount else None

    # --- Сбор итоговых данных ---
    gift_data = {
        "user": sender_id,
        "telegram_sender_id": sender_id,
        "telegram_sender_name": sender_name,
        "telegram_chat_name": chat_name,

        "ton_contract_address": ton_address,
        "name": title,
        "symbol": slug,
        "image_url": image_url,
        "price_ton": price_ton,
        "rarity_level": rarity_level,

        **attr_data  # <-- добавляем backdrop_name, model_name, pattern_name и permille
    }

    # Убираем None и пустые значения
    return {k: v for k, v in gift_data.items() if v is not None}


async def send_to_django_backend(gift_data: dict):
    """
    Отправляет извлеченные данные подарка на Django API.
    """
    if not API_URL:
        logger.error("❌ Переменная DJANGO_GIFT_WEBHOOK_URL не установлена. Пропускаю отправку.")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {AUTH_TOKEN}' if AUTH_TOKEN else '',
    }

    try:
        logger.info("=== 📤 Отправка данных в Django API ===")
        logger.info(f"URL: {API_URL}")
        logger.info(f"Заголовки: {headers}")
        logger.info(f"Тело запроса:\n{json.dumps(gift_data, indent=4, ensure_ascii=False)}")
        logger.info("=======================================")

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
    chat_entity = await client.get_entity(message.chat_id)
    chat_name = utils.get_display_name(chat_entity)

    logger.warning(f"🎁 Найден Star Gift в MSG_ID: {message.id} от {sender_name} ({sender_id}) в чате '{chat_name}'")

    gift_data = extract_gift_data(
        action,
        sender_id=sender_id,
        sender_name=sender_name,
        chat_name=chat_name,
        message=message
    )

    logger.info("--- 📦 Данные для GiftSerializer (JSON-формат) ---")
    print(json.dumps(gift_data, indent=4, ensure_ascii=False))
    logger.info("--------------------------------------------------")

    if gift_data:
        await send_to_django_backend(gift_data)
