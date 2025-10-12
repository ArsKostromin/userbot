import logging
import json
import requests
import config

logger = logging.getLogger(__name__)

# --- КОНФИГУРАЦИЯ БЭКЕНДА ---
# Установите эти переменные окружения!
API_BASE_URL = config.API_BASE_URL
API_URL = f"{API_BASE_URL}/api/gifts/adds-gift/"
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
    
    # Ищем атрибут в списке
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

def extract_gift_data(action) -> dict:
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
    gift_number = None
    slug = getattr(gift_info, 'slug', None)
    
    if slug and '-' in slug:
        number_part = slug.split('-')[-1]
        if number_part.isdigit():
            gift_number = '#' + number_part
        
    image_url = None
    candy_stripe_attr = next((attr for attr in attributes if getattr(attr, 'name', None) == 'Candy Stripe'), None)
    document = getattr(candy_stripe_attr, 'document', None)
    if document:
        image_url = f"https://t.me/sticker/{getattr(document, 'id', '')}"
    
    # --- Формируем данные для Django GiftSerializer ---
    data = {
        "ton_contract_address": ton_address, 
        "name": f"{getattr(gift_info, 'title', 'Gift')} {gift_number}" if gift_number else getattr(gift_info, 'title', 'Gift'),
        "image_url": image_url,
        "price_ton": getattr(gift_info, 'value_amount', None) / 100 if getattr(gift_info, 'value_amount', None) else None, 
        
        # Визуальные компоненты
        "backdrop_name": backdrop_details['name'],
        "model_name": model_details['name'],
        "pattern_name": pattern_details['name'],
        "symbol": slug, 
        "rarity_level": getattr(getattr(gift_info, 'rarity_level', None), 'name', None),

        # Детали редкости
        "model_rarity_permille": model_details['rarity_permille'],
        "model_original_details": model_details['original_details'],
        "pattern_rarity_permille": pattern_details['rarity_permille'],
        "pattern_original_details": pattern_details['original_details'],
        "backdrop_rarity_permille": backdrop_details['rarity_permille'],
        "backdrop_original_details": backdrop_details['original_details'],
    }
    
    # Очищаем словарь от None для чистоты JSON
    return {k: v for k, v in data.items() if v is not None}


async def send_to_django_backend(gift_data: dict, sender_id: int):
    """
    Отправляет извлеченные данные подарка на Django API.
    """
    if not API_URL:
        logger.error("❌ Переменная DJANGO_GIFT_WEBHOOK_URL не установлена. Пропускаю отправку.")
        return

    headers = {
        'Content-Type': 'application/json',
        # Добавьте токен, если используете аутентификацию
        'Authorization': f'Token {AUTH_TOKEN}' if AUTH_TOKEN else '',
    }
    
    # Добавляем ID отправителя, который может понадобиться для связи с пользователем
    gift_data['telegram_sender_id'] = sender_id 

    try:
        response = requests.post(API_URL, json=gift_data, headers=headers, timeout=10)
        response.raise_for_status() 
        logger.info(f"🎉 Данные успешно отправлены в Django. Ответ: {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Ошибка отправки данных в Django (POST {API_URL}): {e}")
        logger.debug(f"Данные, которые не удалось отправить: {gift_data}")


async def handle_star_gift(message, client, **kwargs):
    """
    Основной обработчик для MessageActionStarGiftUnique.
    """
    action = getattr(message, 'action', None)
    if not action or type(action).__name__ != 'MessageActionStarGiftUnique':
        return

    sender_id = getattr(message.sender, 'id', None)

    # 1. Извлекаем данные
    gift_data = extract_gift_data(action)
    
    logger.warning(f"🎁 Найден Star Gift в MSG_ID: {message.id} от пользователя ID: {sender_id}!")
    
    # 2. Логируем данные
    logger.info("--- 📦 Данные для GiftSerializer (JSON-формат) ---")
    print(json.dumps(gift_data, indent=4, ensure_ascii=False))
    logger.info("--------------------------------------------------")
    
    # 3. Отправляем на бэкенд
    if gift_data:
        await send_to_django_backend(gift_data, sender_id)
        
    # ВНИМАНИЕ: Если вы хотите, чтобы это сообщение было отмечено как прочитанное 
    # только после успешной обработки, здесь можно добавить логику.
    # Для целей истории, лучше читать их по умолчанию.