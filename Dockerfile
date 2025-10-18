FROM python:3.11-slim

# --- Устанавливаем зависимости ---
RUN apt-get update && apt-get install -y wget unzip libssl-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# --- Скачиваем готовую TDLib библиотеку ---
RUN wget -O /tmp/tdlib.zip https://github.com/tdlib/td/releases/download/v1.8.26/tdlib.zip && \
    unzip /tmp/tdlib.zip -d /tmp/tdlib && \
    cp /tmp/tdlib/lib/libtdjson.so /usr/local/lib/libtdjson.so && \
    rm -rf /tmp/tdlib /tmp/tdlib.zip && \
    ldconfig

# --- Проверим, что TDLib на месте ---
RUN ls -lh /usr/local/lib/libtdjson.so && echo "✅ TDLib установлена"

# --- Рабочая директория ---
WORKDIR /app

# --- Устанавливаем Python-зависимости ---
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Копируем код ---
COPY . .

# --- Запуск ---
CMD ["/bin/sh", "-c", "sleep 10 && python main.py"]
