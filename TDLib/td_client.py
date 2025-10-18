import os
import json
import logging
from ctypes import CDLL, c_char_p, c_int, c_double
from config import API_ID, API_HASH, PHONE_NUMBER, LOGIN_CODE, SESSION_PATH, LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL

# ==========================
# ЛОГИРОВАНИЕ
# ==========================
logging.basicConfig(format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT, level=LOG_LEVEL)
logger = logging.getLogger(__name__)

# ==========================
# НАСТРОЙКИ TDLib
# ==========================
TDLIB_PATH = os.getenv("TDLIB_PATH", "/usr/local/lib/libtdjson.so")
DB_DIR = os.path.join(SESSION_PATH, "tdlib_db")
FILES_DIR = os.path.join(SESSION_PATH, "tdlib_files")

os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)


class TDLibClient:
    def __init__(self):
        logger.info("🚀 Инициализация TDLib клиента...")
        self.tdjson = CDLL(TDLIB_PATH)
        self.client_id = self.tdjson.td_json_client_create()

        # Настройка типов
        self.tdjson.td_json_client_send.argtypes = [c_int, c_char_p]
        self.tdjson.td_json_client_receive.argtypes = [c_int, c_double]
        self.tdjson.td_json_client_receive.restype = c_char_p

    def send(self, query: dict):
        """Отправка команды в TDLib"""
        self.tdjson.td_json_client_send(self.client_id, json.dumps(query).encode("utf-8"))
        logger.debug(f"➡️ TDLib SEND: {query}")

    def receive(self, timeout=2.0):
        """Получение апдейта"""
        result = self.tdjson.td_json_client_receive(self.client_id, c_double(timeout))
        if result:
            data = json.loads(result.decode("utf-8"))
            logger.debug(f"⬅️ TDLib RECV: {data}")
            return data
        return None

    async def authorize(self):
        """Пошаговая авторизация"""
        import asyncio
        logger.info("🔐 Ожидание авторизации...")
        while True:
            update = self.receive()
            if not update:
                await asyncio.sleep(1)
                continue

            if update.get("@type") != "updateAuthorizationState":
                continue

            state = update["authorization_state"]["@type"]
            logger.info(f"📶 AuthState: {state}")

            if state == "authorizationStateWaitTdlibParameters":
                self.send({
                    "@type": "setTdlibParameters",
                    "parameters": {
                        "database_directory": DB_DIR,
                        "files_directory": FILES_DIR,
                        "use_file_database": True,
                        "use_chat_info_database": True,
                        "use_message_database": True,
                        "use_secret_chats": False,
                        "api_id": int(API_ID),
                        "api_hash": API_HASH,
                        "system_language_code": "ru",
                        "device_model": "Server",
                        "application_version": "1.0",
                        "enable_storage_optimizer": True
                    }
                })

            elif state == "authorizationStateWaitPhoneNumber":
                self.send({
                    "@type": "setAuthenticationPhoneNumber",
                    "phone_number": PHONE_NUMBER
                })

            elif state == "authorizationStateWaitCode":
                logger.info(f"📲 Код авторизации: {LOGIN_CODE}")
                self.send({
                    "@type": "checkAuthenticationCode",
                    "code": LOGIN_CODE
                })

            elif state == "authorizationStateReady":
                logger.info("✅ Авторизация успешно завершена!")
                return True

            elif state == "authorizationStateClosed":
                logger.error("❌ TDLib соединение закрыто.")
                return False
