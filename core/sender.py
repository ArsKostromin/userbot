import logging
from telethon.tl.types import PeerUser, InputPeerUser
from telethon.errors.rpcerrorlist import PeerIdInvalidError, UserIsBlockedError, PeerFloodError
from telethon.client import TelegramClient

logger = logging.getLogger(__name__)

# --- Данные из вашего лога ---

# 1. ПОЛУЧАТЕЛЬ (кому отправляем)
# Мы будем использовать USERNAME, так как это надежнее,
# но ID и HASH тоже можно использовать.
RECIPIENT_USERNAME = "jhgvcbcg"
RECIPIENT_ID = 1207534564
RECIPIENT_ACCESS_HASH = -8813161918532140746

# 2. ИСТОЧНИК (откуда берем сообщение)
# Это название чата, из которого нужно переслать
SOURCE_CHAT_NAME = "[Ɐ] r" 

# 3. ПОДАРОК (что пересылаем)
# ID того самого сообщения с "Snake Box"
GIFT_MESSAGE_ID = 41

# ---------------------------------


async def send_gift_once(client: TelegramClient):
    """
    Выполняет ОДНУ пересылку "подарка" (сообщения)
    указанному пользователю.
    """
    logger.info(f"🚀 Начинаю операцию по отправке подарка...")

    try:
        # 1. Находим получателя
        # Использование username - самый простой способ
        logger.info(f"Ищу получателя: @{RECIPIENT_USERNAME}")
        
        # Альтернативно, если username нет, но есть ID и HASH:
        # target_user = InputPeerUser(user_id=RECIPIENT_ID, access_hash=RECIPIENT_ACCESS_HASH)
        
        target_user = await client.get_entity(RECIPIENT_USERNAME)
        logger.info(f"✅ Получатель найден: {target_user.first_name} (ID: {target_user.id})")

        # 2. Находим чат-источник
        logger.info(f"Ищу чат-источник: '{SOURCE_CHAT_NAME}'")
        source_chat = await client.get_entity(SOURCE_CHAT_NAME)
        logger.info(f"✅ Чат-источник найден (ID: {source_chat.id})")

        # 3. Пересылаем сообщение
        
        await client.transfer_gift(
            entity=target_user,           # Кому (наш получатель)
            messages=GIFT_MESSAGE_ID,     # Какое сообщение
            from_peer=source_chat         # Откуда (наш чат-источник)
        )
        
        logger.info("✅🎁 Подарок успешно переслан!")

    except PeerIdInvalidError:
        logger.error(f"❌ Не удалось найти получателя @{RECIPIENT_USERNAME} или чат '{SOURCE_CHAT_NAME}'.")
        logger.error("Убедитесь, что userbot состоит в этом чате и что username/название верны.")
    except UserIsBlockedError:
        logger.warning(f"⚠️ Пользователь @{RECIPIENT_USERNAME} заблокировал этого юзербота.")
    except PeerFloodError:
        logger.error("❌ Слишком много запросов (PeerFloodError). Временная блокировка. Попробуйте позже.")
    except Exception as e:
        logger.exception(f"❌ Непредвиденная ошибка при отправке: {e}")