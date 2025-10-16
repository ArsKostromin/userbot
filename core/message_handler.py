import logging
import json
import requests
import config
from telethon import utils
from .media_utils import download_thumbnail_image

logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ БЭКЕНДА ---
API_BASE_URL = getattr(config, 'API_BASE_URL', None)
API_URL = f"{API_BASE_URL}/Inventory/adds-gift/" if API_BASE_URL else None
AUTH_TOKEN = getattr(config, 'API_TOKEN', None)


def extract_gift_data(action) -> dict:
    gift_info = getattr(action, 'gift', None)
    if not gift_info:
        logger.warning("⚠️ Объект 'gift' не найден в action, обработка невозможна.")
        return {}

    attributes = getattr(gift_info, 'attributes', [])
    
    model_attr = next((a for a in attributes if type(a).__name__ == 'StarGiftAttributeModel'), None)
    pattern_attr = next((a for a in attributes if type(a).__name__ == 'StarGiftAttributePattern'), None)
    backdrop_attr = next((a for a in attributes if type(a).__name__ == 'StarGiftAttributeBackdrop'), None)

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
    }

    return {k: v for k, v in gift_data.items() if v is not None}


async def send_to_django_backend(gift_data: dict):
    if not API_URL:
        logger.error("❌ API_URL не установлен. Пропускаю отправку.")
        return

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Token {AUTH_TOKEN}' if AUTH_TOKEN else '',
    }
    
    try:
        logger.info("=== 📤 Отправка данных в Django API ===")
        logger.info(json.dumps(gift_data, indent=4, ensure_ascii=False))
        response = requests.post(API_URL, json=gift_data, headers=headers, timeout=10)

        if 200 <= response.status_code < 300:
            logger.info(f"🎉 Успешно отправлено! Код ответа: {response.status_code}")
        else:
            logger.error(f"⚠️ Ошибка {response.status_code} при POST в Django: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка при POST {API_URL}: {e}")


async def handle_star_gift(message, client, **kwargs):
    action = getattr(message, 'action', None)
    if not action or type(action).__name__ != 'MessageActionStarGiftUnique':
        return

    sender_id = getattr(message.sender, 'id', None)
    sender_name = utils.get_display_name(message.sender)
    chat = await message.get_chat()
    chat_name = utils.get_display_name(chat)

    logger.warning(f"🎁 Найден Star Gift в MSG_ID: {message.id} от {sender_name} ({sender_id}) в '{chat_name}'")

    gift_data = extract_gift_data(action)

    # 🧠 ВАЖНО: добавляем системные поля, нужные для передачи подарка
    gift_data.update({
        "peer_id": chat.id,                            # где лежит подарок
        "msg_id": message.id,                          # id конкретного сообщения
        "access_hash": getattr(chat, 'access_hash', None),  # нужен для InvokeWithMsgId
        "from_user_id": sender_id,                     # кто прислал подарок
        "chat_name": chat_name,                        # откуда
    })

    # --- thumbnail ---
    image_url = None
    gift_info = getattr(action, 'gift', None)
    if gift_info:
        model_attr = next((a for a in getattr(gift_info, 'attributes', []) if type(a).__name__ == 'StarGiftAttributeModel'), None)
        document = getattr(model_attr, 'document', None)
        slug = gift_data.get('symbol')
        if document and slug:
            image_url = await download_thumbnail_image(client, document, slug)

    gift_data['image_url'] = image_url or "https://teststudiaorbita.ru/media/avatars/diamond.jpg"

    gift_data["user"] = sender_id

    logger.info("--- 📦 Данные для Django ---")
    logger.info(json.dumps(gift_data, indent=4, ensure_ascii=False))
    logger.info("-------------------------------------------")

    await send_to_django_backend(gift_data)
