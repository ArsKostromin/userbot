FROM python:3.11-slim

# --- Устанавливаем зависимости для TDLib ---
RUN apt-get update && apt-get install -y \
    git cmake g++ make wget unzip zlib1g-dev libssl-dev && \
    rm -rf /var/lib/apt/lists/*

# --- Качаем и собираем TDLib ---
RUN git clone --branch v1.8.26 --depth 1 https://github.com/tdlib/td.git /tmp/tdlib && \
    mkdir /tmp/tdlib/build && cd /tmp/tdlib/build && \
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=/usr/local .. && \
    cmake --build . --target install -j$(nproc) && \
    rm -rf /tmp/tdlib

# --- Проверяем, что библиотека установлена ---
RUN ls -lh /usr/local/lib/libtdjson.so && echo "✅ TDLib собрана и установлена"

# --- Рабочая директория ---
WORKDIR /app

# --- Устанавливаем Python-зависимости ---
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# --- Копируем код ---
COPY . .

# --- Запуск ---
CMD ["/bin/sh", "-c", "sleep 10 && python main.py"]
