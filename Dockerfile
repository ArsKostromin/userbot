FROM python:3.11-slim

# --- Устанавливаем системные зависимости и TDLib ---
RUN apt-get update && apt-get install -y \
    git cmake g++ make zlib1g-dev libssl-dev gperf wget unzip && \
    git clone --depth=1 https://github.com/tdlib/td.git /td && \
    mkdir /td/build && cd /td/build && \
    cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX:PATH=/usr/local .. && \
    cmake --build . --target install -j$(nproc) && \
    rm -rf /td && \
    ldconfig

WORKDIR /app

COPY requirements.txt .

# Устанавливаем Python-зависимости
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["/bin/sh", "-c", "sleep 10 && python main.py"]
