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
    Извлекает все необходимые поля, работая с объектами как с "черными ящиками" (просто извлекая строки/атрибуты).
    """
    # Получаем объект 'gift' из 'action'
    gift_info = getattr(action, 'gift', None)
    if not gift_info:
        return {}

    # --- Извлечение деталей атрибутов ---
    attributes = getattr(gift_info, 'attributes', [])
    
    # Model (Candy Stripe)
    model_details = get_attribute_details(attributes, 'Candy Stripe')
    # Backdrop (Aquamarine)
    backdrop_details = get_attribute_details(attributes, 'Aquamarine')
    # Pattern (Stocking)
    pattern_details = get_attribute_details(attributes, 'Stocking')
            
    # --- Обработка номера подарка и Slug ---
    ton_address = getattr(gift_info, 'slug', None) or str(getattr(gift_info, 'id', ''))
    gift_number = None
    
    slug = getattr(gift_info, 'slug', None)
    if slug and '-' in slug:
        number_part = slug.split('-')[-1]
        if number_part.isdigit():
            gift_number = '#' + number_part
        
    # --- Сборка URL изображения ---
    image_url = None
    # Ищем атрибут "Candy Stripe" снова, чтобы получить доступ к 'document'
    candy_stripe_attr = next((attr for attr in attributes if getattr(attr, 'name', None) == 'Candy Stripe'), None)
    
    document = getattr(candy_stripe_attr, 'document', None)
    if document:
        # Формируем ссылку на стикер
        image_url = f"https://t.me/sticker/{getattr(document, 'id', '')}"
    
    # --- Информация об отправителе ---
    sender_info = {}
    if message and hasattr(message, 'sender_id'):
        sender_id = getattr(message, 'sender_id', None)
        if sender_id:
            sender_info = {
                "sender_id": sender_id,
                "sender_username": None,  # Будет заполнено позже
                "sender_first_name": None,
                "sender_last_name": None
            }

    # --- Сборка финального словаря ---
    data = {
        "ton_contract_address": ton_address, 
        # name: Добавляем номер подарка в название, если он найден
        "name": f"{getattr(gift_info, 'title', 'Gift')} {gift_number}" if gift_number else getattr(gift_info, 'title', 'Gift'),
        "image_url": image_url,
        # value_amount - это сумма в минимальных единицах валюты.
        "price_ton": getattr(gift_info, 'value_amount', None) / 100 if getattr(gift_info, 'value_amount', None) else None, 
        "backdrop": backdrop_details['name'],
        "symbol": slug,
        
        # НОВЫЕ ПОЛЯ РЕДКОСТИ И ДЕТАЛИ:
        "model_name": model_details['name'],
        "model_rarity_permille": model_details['rarity_permille'],
        "model_original_details": model_details['original_details'],
        
        "pattern_name": pattern_details['name'],
        "pattern_rarity_permille": pattern_details['rarity_permille'],
        "pattern_original_details": pattern_details['original_details'],
        
        "backdrop_name": backdrop_details['name'],
        "backdrop_rarity_permille": backdrop_details['rarity_permille'],
        "backdrop_original_details": backdrop_details['original_details'],

        # Общая редкость подарка
        "rarity_level": getattr(getattr(gift_info, 'rarity_level', None), 'name', None),
        
        # Информация об отправителе
        "sender_info": sender_info
    }
    
    # Очищаем данные, удаляя None-значения для чистоты вывода, кроме основных полей
    data = {k: v for k, v in data.items() if v is not None} 
    
    return data


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
