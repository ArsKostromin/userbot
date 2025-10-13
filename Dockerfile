FROM python:3.11-slim

# Устанавливаем системные зависимости для Pillow и python-lottie.
# libjpeg-dev и libgif-dev нужны для Pillow
# libcairo2-dev и libpango1.0-dev нужны для python-lottie
# pkg-config, git нужны для сборки сложных пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Устанавливаем Python-зависимости
# 💡 ИСПРАВЛЕНИЕ: Обновляем pip и устанавливаем зависимости в одной команде.
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/bin/sh", "-c", "sleep 10 && python main.py"]
