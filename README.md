# Userbot для мониторинга Star Gifts

Этот userbot мониторит чат `@kupil_prodal_l9m` и автоматически отправляет найденные Star Gifts в Django API.

## Структура проекта

```
userbot/
├── __init__.py          # Инициализация пакета
├── main.py             # Основной файл запуска
├── config.py           # Конфигурация
├── telegram_client.py  # Работа с Telegram API
├── message_handler.py  # Обработка сообщений
├── gift_processor.py   # Обработка данных подарков
├── api_client.py       # Работа с Django API
├── requirements.txt    # Зависимости
└── Dockerfile         # Docker конфигурация
```

## Переменные окружения

```env
# Telegram API
API_ID=your_telegram_api_id
API_HASH=your_telegram_api_hash
PHONE_NUMBER=your_phone_number
LOGIN_CODE=your_login_code

# Django API
API_BASE_URL=http://web:8000
API_TOKEN=your_django_api_token
USER_ID=1
```

## Запуск

```bash
python main.py
```

## Docker

```bash
docker-compose up userbot
```
