FROM python:3.11-slim

# --- Устанавливаем системные зависимости ---
RUN apt-get update && apt-get install -y wget unzip libssl-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# --- Скачиваем готовую TDLib ---
RUN mkdir -p /usr/local/lib && \
    wget -O /usr/local/lib/libtdjson.so https://github.com/tdlib/td/releases/download/v1.8.26/tdlib.zip && \
    unzip /usr/local/lib/libtdjson.so -d /usr/local/lib || true

# --- Проверим, что библиотека на месте ---
RUN ls -lh /usr/local/lib/libtdjson.so || echo "⚠️ TDLib not found!"

# --- Рабочая директория ---
WORKDIR /app

# --- Копируем зависимости Python ---
COPY requirements.txt .

# --- Устанавливаем Python-зависимости ---
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Копируем весь проект ---
COPY . .

# --- Запуск ---
CMD ["/bin/sh", "-c", "sleep 10 && python main.py"]
