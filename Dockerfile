FROM python:3.11-slim

# Устанавливаем системные зависимости: Node.js и пакеты для Pillow.
# Node.js и npm нужны для установки tgs-converter.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    libgif-dev \
    nodejs \
    npm \
    # 💡 ИСПРАВЛЕНИЕ: Используем --prefix /usr/local, чтобы tgs-converter попал в /usr/local/bin, 
    # который гарантированно находится в PATH.
    && npm install -g tgs-converter --prefix /usr/local \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/bin/sh", "-c", "sleep 10 && python main.py"]
