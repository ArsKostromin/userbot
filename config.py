"""
Конфигурация для userbot
Содержит все настройки и переменные окружения
"""
import os

# TELEGRAM API НАСТРОЙКИ
# Получаем API ключи из переменных окружения
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

# НАСТРОЙКИ АВТОРИЗАЦИИ
# Номер телефона в международном формате (например: +1234567890)
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
# Код авторизации из SMS (получается автоматически при первом запуске)
LOGIN_CODE = os.getenv("LOGIN_CODE")

# DJANGO API НАСТРОЙКИ
# URL Django API (по умолчанию web:8000 для Docker)
API_BASE_URL = os.getenv("API_BASE_URL", "http://web:8000")
API_TOKEN = os.getenv("API_TOKEN")        # Токен для авторизации в Django API
USER_ID = os.getenv("USER_ID")            # ID пользователя, которому добавляем подарки

# НАСТРОЙКИ ЛОГИРОВАНИЯ
# Формат логов
LOG_FORMAT = 'telethon-userbot | %(asctime)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_LEVEL = 'INFO'  # Уровень логирования (DEBUG, INFO, WARNING, ERROR)

# ПУТИ К ФАЙЛАМ
# Путь к файлу сессии Telegram
SESSION_PATH = "session/userbot"

# TDLib НАСТРОЙКИ
TDLIB_LIBRARY_PATH = os.getenv("TDLIB_LIBRARY_PATH", "./tdlib/libtdjson.so")
TDLIB_DATABASE_DIR = os.getenv("TDLIB_DATABASE_DIR", "tdlib_database")
TDLIB_FILES_DIR = os.getenv("TDLIB_FILES_DIR", "tdlib_files")
TDLIB_USE_TEST_DC = os.getenv("TDLIB_USE_TEST_DC", "False").lower() in ("true", "1", "yes")