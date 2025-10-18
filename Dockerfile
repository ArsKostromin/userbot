FROM python:3.11-slim

# Устанавливаем системные зависимости для Pillow и, возможно, для сборки lottie-python.
# libjpeg-dev и libgif-dev нужны для Pillow
# 💡 ИСПРАВЛЕНИЕ: Удаляем Node.js/npm. Возвращаем инструменты сборки, чтобы обеспечить компиляцию lottie-python.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    libgif-dev \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/bin/sh", "-c", "sleep 10 && python main.py"]
