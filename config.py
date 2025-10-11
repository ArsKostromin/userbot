"""
Конфигурация для userbot
"""
import os

# Telegram API настройки
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
LOGIN_CODE = os.getenv("LOGIN_CODE")

# Целевой чат для мониторинга
TARGET_CHAT_USERNAME = '@kupil_prodal_l9m'

# Django API настройки
API_BASE_URL = os.getenv("API_BASE_URL", "http://web:8000")
API_TOKEN = os.getenv("API_TOKEN")
USER_ID = os.getenv("USER_ID")

# Настройки логирования
LOG_FORMAT = 'telethon-userbot | %(asctime)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = 'INFO'

# Путь к сессии
SESSION_PATH = "session/userbot"
