import logging
import json
import requests
from telethon import utils
from telethon.tl.types import MessageActionStarGiftUnique

logger = logging.getLogger(__name__)

API_BASE_URL = "https://example.com/api"  # твой config.API_BASE_URL
API_URL = f"{API_BASE_URL}/Inventory/adds-gift/"
AUTH_TOKEN = "YOUR_TOKEN_HERE"  # config.API_TOKEN


def parse_attribute(attr):
    """
    Рекурсивный парсер StarGift атрибута
    """
    if not attr:
        return {}

    data = {
        "type": type(attr).__name__,
        "name": getattr(attr, "name", None),
        "rarity_permille": getattr(attr, "rarity_permille", None),
    }

    # Документ (если есть)
    document = getattr(attr, "document", None)
    if document:
        data["document"] = {
            "id": getattr(document, "id", None),
            "file_name": getattr(document, "file_name", None),
            "mime_type": getattr(document, "mime_type", None),
            "size": getattr(document, "size", None),
            "width": getattr(document, "attributes", [None])[0].w if getattr(document, "attributes", None) else None,
            "height": getattr(document, "attributes", [None])[0].h if getattr(document, "attributes", None) else None,
            "emoji": getattr(document.attributes[1], "alt", None) if len(document.attributes) > 1 else None,
            "stickerset_id": getattr(getattr(document.attributes[1], "stickerset", None), "id", None)
            if len(document.attributes) > 1 else None,
        }

    # Оригинальные детали (для StarGiftAttributeOriginalDetails)
    original = getattr(attr, "original_details", None)
    if original:
        data["original_details"] = {
            "recipient_id": getattr(original, "recipient_id", None).user_id
            if getattr(original, "recipient_id", None) else None,
            "sender_id": getattr(original, "sender_id", None).user_id
            if getattr(original, "sender_id", None) else None,
            "date": getattr(original, "date", None),
            "message": getattr(getattr(original, "message", None), "text", None)
        }

    return data


def extract_gift_data(action: MessageActionStarGiftUnique, sender_id=None, sender_name=None, chat_name=None, message=None):
    """
    Полный парсер StarGift с извлечением всех атрибутов и документов
    """
    gift = getattr(action, "gift", None)
    if not gift:
        return {}

    # Основные поля
    gift_data = {
        "gift_id": getattr(gift, "gift_id", None),
        "title": getattr(gift, "title", None),
        "slug": getattr(gift, "slug", None),
        "num": getattr(gift, "num", None),
        "rarity_permille": getattr(gift, "rarity_permille", None),
        "attributes": [],
        "user": sender_id,
        "telegram_sender_id": sender_id,
        "telegram_sender_name": sender_name,
        "telegram_chat_name": chat_name,
    }

    # Все атрибуты
    for attr in getattr(gift, "attributes", []):
        gift_data["attributes"].append(parse_attribute(attr))

    # Попытка достать image_url
    image_url = None
    if message and getattr(message, "media", None) and getattr(message.media, "document", None):
        doc = message.media.document
        if getattr(doc, "id", None):
            image_url = f"https://t.me/sticker/{doc.id}"
    elif hasattr(gift, "document") and getattr(gift.document, "id", None):
        image_url = f"https://t.me/sticker/{gift.document.id}"
    else:
        image_url = "https://cdn-icons-png.flaticon.com/512/3989/3989685.png"

    gift_data["image_url"] = image_url

    return gift_data


async def handle_star_gift(message, client, **kwargs):
    action = getattr(message, "action", None)
    if not action or type(action).__name__ != "MessageActionStarGiftUnique":
        return

    sender_id = getattr(message.sender, "id", None)
    sender_name = utils.get_display_name(message.sender)
    chat_entity = await client.get_entity(message.chat_id)
    chat_name = utils.get_display_name(chat_entity)

    logger.warning(f"🎁 Найден Star Gift в MSG_ID: {message.id} от {sender_name} ({sender_id}) в чате '{chat_name}'")

    gift_data = extract_gift_data(action, sender_id, sender_name, chat_name, message)

    logger.info("--- 📦 Данные для GiftSerializer (JSON-формат) ---")
    print(json.dumps(gift_data, indent=4, ensure_ascii=False))
    logger.info("--------------------------------------------------")

    if gift_data:
        await send_to_django_backend(gift_data)


async def send_to_django_backend(gift_data: dict):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {AUTH_TOKEN}" if AUTH_TOKEN else "",
    }
    try:
        response = requests.post(API_URL, json=gift_data, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"🎉 Успешно отправлено! Код ответа: {response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка при POST {API_URL}: {e}")
