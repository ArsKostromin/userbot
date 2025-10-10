import os
import asyncio
import logging
import json 

# --- КОНФИГУРАЦИЯ ---
# Для работы этого скрипта все равно необходим установленный пакет telethon.
# Мы не импортируем конкретные типы, но используем TelegramClient.
from telethon import TelegramClient 

TARGET_CHAT_USERNAME = '@kupil_prodal_l9m' 

# --- НАСТРОЙКА ЛОГИРОВАНИЯ ---
logging.basicConfig(
    format='telethon-userbot | %(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- ПОЛУЧЕНИЕ КЛЮЧЕЙ API ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
api_id_str = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

try:
    if not api_id_str or not api_hash:
        raise ValueError("Не найдены переменные окружения API_ID или API_HASH.")
    api_id = int(api_id_str)
except (ValueError, TypeError) as e:
    logger.error(f"❌ Критическая ошибка: {e}")
    logger.error("➡️ Пожалуйста, убедитесь, что API_ID является числом, и обе переменные установлены.")
    exit(1)

# --- ИНИЦИАЛИЗАЦИЯ КЛИЕНТА TELEGRAM ---
client = TelegramClient("session/userbot", api_id, api_hash)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

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

def extract_gift_data(action) -> dict:
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
        "rarity_level": getattr(getattr(gift_info, 'rarity_level', None), 'name', None)
    }
    
    # Очищаем данные, удаляя None-значения для чистоты вывода, кроме основных полей
    data = {k: v for k, v in data.items() if v is not None} 
    
    return data

# --- ОСНОВНАЯ ФУНКЦИЯ ---

async def main():
    async with client:
        if not await client.is_user_authorized():
            logger.error("❌ Авторизация не удалась.")
            return

        me = await client.get_me()
        user_info = f"{me.first_name or ''} (@{me.username})" if me else "Unknown User"
        logger.info(f"✅ Успешная авторизация под аккаунтом: {user_info.strip()}")
        
        try:
            logger.info(f"🔎 Ищем чат: {TARGET_CHAT_USERNAME}...")
            chat = await client.get_entity(TARGET_CHAT_USERNAME)
            chat_name = getattr(chat, 'title', getattr(chat, 'username', str(chat.id)))
            logger.info(f"👍 Чат '{chat_name}' найден. Начинаю анализ последних сообщений...")

        except Exception as e:
            logger.error(f"❌ Произошла непредвиденная ошибка при поиске чата: {e}")
            return

        message_count = 0
        gift_data = None
        
        # Перебираем сообщения
        async for message in client.iter_messages(chat, limit=50): 
            message_count += 1
            
            # 💡 ПРОВЕРКА ТИПА ПО ИМЕНИ СТРОКИ:
            if getattr(message, 'action', None) and type(message.action).__name__ == 'MessageActionStarGiftUnique':
                
                # 1. Извлекаем и сохраняем данные в переменную
                gift_data = extract_gift_data(message.action)
                
                logger.warning(f"🎁 Найден Star Gift в MSG_ID: {getattr(message, 'id', 'N/A')}! Извлекаю данные...")
                
                break 

        logger.info(f"✅ Анализ чата '{chat_name}' завершен. Всего обработано сообщений: {message_count}.")

        if gift_data:
            # 2. Выводим сохраненные данные в консоль
            logger.info("--- 📦 Данные для GiftSerializer (JSON-формат) ---")
            print(json.dumps(gift_data, indent=4, ensure_ascii=False))
            logger.info("--------------------------------------------------")
        else:
            logger.info("ℹ️ Уникальный Star Gift не найден в обработанных сообщениях.")

if __name__ == "__main__":
    asyncio.run(main())