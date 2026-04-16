# Stage 1: Build
# Используем конкретную версию Rust на базе Debian Bookworm
FROM rust:1.88-bookworm AS builder

WORKDIR /app

# Установка необходимых системных зависимостей для сборки
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . .
RUN cargo build --release

# Stage 2: Runtime
# Используем ту же версию ОС (Bookworm), что и при сборке
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
    libssl3 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем бинарный файл из этапа сборки
COPY --from=builder /app/target/release/task_service /usr/local/bin/task_service

# Указываем имя бинарника для запуска
CMD ["task_service"]
