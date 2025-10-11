import os
import asyncio
import logging
import json
from telethon import TelegramClient, events

# --- КОНФИГУРАЦИЯ ---
api_id_str = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

if not api_id_str or not api_hash:
    raise ValueError("Не найдены переменные окружения API_ID или API_HASH.")

api_id = int(api_id_str)
client = TelegramClient("session/userbot", api_id, api_hash)

# --- ЛОГИРОВАНИЕ ---
logging.basicConfig(
    format='telethon-userbot | %(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- ФУНКЦИИ EXTRACT ---
# (копируем сюда твои функции extract_gift_data и get_attribute_details)
def get_attribute_details(gift_info_attributes: list, name: str) -> dict:
    attr_data = {'name': None, 'rarity_permille': None, 'original_details': None}
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
    data = {
        "ton_contract_address": ton_address, 
        "name": f"{getattr(gift_info, 'title', 'Gift')} {gift_number}" if gift_number else getattr(gift_info, 'title', 'Gift'),
        "image_url": image_url,
        "price_ton": getattr(gift_info, 'value_amount', None) / 100 if getattr(gift_info, 'value_amount', None) else None, 
        "backdrop": backdrop_details['name'],
        "symbol": slug,
        "model_name": model_details['name'],
        "model_rarity_permille": model_details['rarity_permille'],
        "model_original_details": model_details['original_details'],
        "pattern_name": pattern_details['name'],
        "pattern_rarity_permille": pattern_details['rarity_permille'],
        "pattern_original_details": pattern_details['original_details'],
        "backdrop_name": backdrop_details['name'],
        "backdrop_rarity_permille": backdrop_details['rarity_permille'],
        "backdrop_original_details": backdrop_details['original_details'],
        "rarity_level": getattr(getattr(gift_info, 'rarity_level', None), 'name', None)
    }
    return {k: v for k, v in data.items() if v is not None}

# --- HANDLER НОВЫХ ПОДАРКОВ ---
@client.on(events.NewMessage)
async def new_message_handler(event):
    message = event.message
    if getattr(message, 'action', None) and type(message.action).__name__ == 'MessageActionStarGiftUnique':
        gift_data = extract_gift_data(message.action)
        logger.warning(f"🎁 Новый NFT Star Gift в чате {getattr(message, 'chat_id', 'Unknown')}, MSG_ID: {getattr(message, 'id', 'N/A')}")
        print(json.dumps(gift_data, indent=4, ensure_ascii=False))

# --- MAIN ---
async def main():
    await client.start()
    me = await client.get_me()
    logger.info(f"✅ Userbot авторизован: {me.first_name} (@{me.username})")
    logger.info("🔄 Слушаю новые NFT подарки...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
