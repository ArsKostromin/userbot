"""
Модуль для обработки данных о подарках
Извлекает информацию из Star Gift сообщений Telegram
"""
import logging

logger = logging.getLogger(__name__)


def get_attribute_details(gift_info_attributes: list, name: str) -> dict:
    """
    Ищет атрибут по имени, используя getattr() вместо явных типов.
    """
    attr_data = {
        'name': None,
        'rarity_permille': None,
        'original_details': None
    }
    
    # Ищем атрибут в списке по его имени
    target_attr = next((attr for attr in gift_info_attributes if getattr(attr, 'name', None) == name), None)
    
    if target_attr:
        attr_data['name'] = getattr(target_attr, 'name', None)
        
        # rarity_permille
        attr_data['rarity_permille'] = getattr(target_attr, 'rarity_permille', None)
        
        # StarGiftAttributeOriginalDetails 
        original_details = getattr(target_attr, 'original_details', None)
        if original_details:
            attr_data['original_details'] = {
                'id': getattr(original_details, 'id', None),
                'type': getattr(original_details, 'type', None),
                'name': getattr(original_details, 'name', None),
            }
    return attr_data


def extract_gift_data(action, message) -> dict:
    """
    Универсальный парсер StarGift, вытаскивает атрибуты по типу, а не по имени.
    """
    gift_info = getattr(action, 'gift', None)
    if not gift_info:
        return {}

    attributes = getattr(gift_info, 'attributes', [])

    # --- Достаём атрибуты по типу ---
    model_attr = next((a for a in attributes if a.__class__.__name__ == "StarGiftAttributeModel"), None)
    pattern_attr = next((a for a in attributes if a.__class__.__name__ == "StarGiftAttributePattern"), None)
    backdrop_attr = next((a for a in attributes if a.__class__.__name__ == "StarGiftAttributeBackdrop"), None)

    def attr_details(attr):
        if not attr:
            return {"name": None, "rarity_permille": None, "original_details": None}
        return {
            "name": getattr(attr, "name", None),
            "rarity_permille": getattr(attr, "rarity_permille", None),
            "original_details": getattr(attr, "original_details", None)
        }

    model_details = attr_details(model_attr)
    pattern_details = attr_details(pattern_attr)
    backdrop_details = attr_details(backdrop_attr)

    # --- TON и slug ---
    ton_address = getattr(gift_info, 'slug', None) or str(getattr(gift_info, 'id', ''))
    slug = getattr(gift_info, 'slug', None)

    # --- Картинка ---
    image_url = None
    for attr in attributes:
        document = getattr(attr, 'document', None)
        if document and getattr(document, 'id', None):
            image_url = f"https://t.me/sticker/{getattr(document, 'id')}"
            break
    if not image_url:
        image_url = getattr(gift_info, 'media_url', None) or getattr(gift_info, 'thumb_url', None) or "https://cdn-icons-png.flaticon.com/512/3989/3989685.png"

    sender_id = getattr(message, 'sender_id', None)
    sender_name = getattr(message.sender, 'first_name', None) if hasattr(message, 'sender') else None

    data = {
        "id": getattr(gift_info, 'id', None),
        "user": sender_id,
        "telegram_sender_id": sender_id,
        "telegram_sender_name": sender_name,
        "telegram_chat_name": getattr(message.chat, 'title', None) if hasattr(message, 'chat') else None,

        "ton_contract_address": ton_address,
        "name": getattr(gift_info, 'title', 'Gift'),
        "symbol": slug,
        "image_url": image_url,
        "price_ton": getattr(gift_info, 'value_amount', None) / 100 if getattr(gift_info, 'value_amount', None) else None,
        "rarity_level": getattr(getattr(gift_info, 'rarity_level', None), 'name', None),

        "model_name": model_details["name"],
        "model_rarity_permille": model_details["rarity_permille"],
        "model_original_details": model_details["original_details"],

        "pattern_name": pattern_details["name"],
        "pattern_rarity_permille": pattern_details["rarity_permille"],
        "pattern_original_details": pattern_details["original_details"],

        "backdrop_name": backdrop_details["name"],
        "backdrop_rarity_permille": backdrop_details["rarity_permille"],
        "backdrop_original_details": backdrop_details["original_details"],
    }

    return {k: v for k, v in data.items() if v is not None}


async def get_sender_info(client, sender_id):
    """
    Получает информацию об отправителе по его ID
    """
    try:
        sender = await client.get_entity(sender_id)
        return {
            "sender_id": sender_id,
            "sender_username": getattr(sender, 'username', None),
            "sender_first_name": getattr(sender, 'first_name', None),
            "sender_last_name": getattr(sender, 'last_name', None)
        }
    except Exception as e:
        logger.warning(f"⚠️ Не удалось получить информацию об отправителе {sender_id}: {e}")
        return {
            "sender_id": sender_id,
            "sender_username": None,
            "sender_first_name": None,
            "sender_last_name": None
        }