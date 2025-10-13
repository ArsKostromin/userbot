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


def get_attribute_details(gift_info_attributes: list, name: str) -> dict:
    """
    Извлекает имя, permille и оригинальные детали атрибута (модель, фон, узор).
    """
    attr_data = {
        'name': None,
        'rarity_permille': None,
        'original_details': None
    }
    
    target_attr = next((attr for attr in gift_info_attributes if getattr(attr, 'name', None) == name), None)
    
    if target_attr:
        attr_data['name'] = getattr(target_attr, 'name', None)
        attr_data['rarity_permille'] = getattr(target_attr, 'rarity_permille', None)
        
        original_details = getattr(target_attr, 'original_details', None)
        if original_details:
            attr_data['original_details'] = {
                'id': getattr(original_details, 'id', None),
                'type': getattr(original_details, 'type', None),
                'name': getattr(original_details, 'name', None),
            }
    return attr_data


def extract_gift_data(action, sender_id=None, sender_name=None, chat_name=None) -> dict:
    """
    Извлекает все необходимые поля из action для GiftSerializer.
    """
    gift_info = getattr(action, 'gift', None)
    if not gift_info:
        return {}

    attributes = getattr(gift_info, 'attributes', [])
    model_details = get_attribute_details(attributes, 'Candy Stripe')
    backdrop_details = get_attribute_details(attributes, 'Aquamarine')
    pattern_details = get_attribute_details(attributes, 'Stocking')

    ton_address = getattr(gift_info, 'slug', None) or str(getattr(gift_info, 'id', ''))
    slug = getattr(gift_info, 'slug', None)
    title = getattr(gift_info, 'title', 'Gift')

    # --- 🖼 Попытка достать реальный image_url ---
    image_url = None
    document = getattr(gift_info, 'document', None)
    if document and getattr(document, 'id', None):
        image_url = f"https://t.me/sticker/{getattr(document, 'id')}"
    elif hasattr(gift_info, 'media_url'):
        image_url = getattr(gift_info, 'media_url')
    elif hasattr(gift_info, 'thumb_url'):
        image_url = getattr(gift_info, 'thumb_url')

    # --- 🧠 Формируем данные для Django ---
    data = {
        "user": sender_id,  # можно заменить на sender_name, если нужно имя
        "telegram_sender_id": sender_id,
        "telegram_sender_name": sender_name,
        "telegram_chat_name": chat_name,

        "ton_contract_address": ton_address,
        "name": title,
        "symbol": slug,
        "image_url": image_url,
        "price_ton": getattr(gift_info, 'value_amount', None) / 100 if getattr(gift_info, 'value_amount', None) else None,

        "rarity_level": getattr(getattr(gift_info, 'rarity_level', None), 'name', None),
        "backdrop_name": backdrop_details['name'],
        "model_name": model_details['name'],
        "pattern_name": pattern_details['name'],

        "model_rarity_permille": model_details['rarity_permille'],
        "pattern_rarity_permille": pattern_details['rarity_permille'],
        "backdrop_rarity_permille": backdrop_details['rarity_permille'],
    }

    # Убираем None и пустые значения
    return {k: v for k, v in data.items() if v is not None}


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

    gift_data = extract_gift_data(action, sender_id=sender_id, sender_name=sender_name, chat_name=chat_name)

    logger.info("--- 📦 Данные для GiftSerializer (JSON-формат) ---")
    print(json.dumps(gift_data, indent=4, ensure_ascii=False))
    logger.info("--------------------------------------------------")

    if gift_data:
        await send_to_django_backend(gift_data)

    # Тут можно добавить отметку сообщения как прочитанного после успешной обработки
