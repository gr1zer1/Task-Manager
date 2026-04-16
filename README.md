# Task Manager - Distributed Task Management System

Полнофункциональная система управления задачами с использованием микросервисной архитектуры.

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Bot (Python)                    │
│              - Создание задач                               │
│              - Просмотр назначенных задач                   │
│              - Отметить как выполненные                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Task Service (Rust)                        │
│              - CRUD операции с задачами                     │
│              - JWT аутентификация                           │
│              - Публикация событий в RabbitMQ                │
└──────────────────────┬──────────────────────────────────────┘
                       │ Events
                       ▼
┌─────────────────────────────────────────────────────────────┐
│    RabbitMQ - Message Broker                                │
│    - task.created                                           │
│    - task.updated                                           │
│    - task.deleted                                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Event Consumer Service (Python)                     │
│              - Обработка событий                            │
│              - Кэширование данных                           │
│              - Нотификации                                  │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Быстрый старт

### Предварительные требования
- Docker & Docker Compose
- Python 3.11+ (для локальной разработки)
- Git

### Установка с Docker (рекомендуется)

```bash
# Клонировать репозиторий
git clone <repo_url>
cd task_manager

# Создать .env файл
cp .env.example .env

# Заполнить необходимые значения в .env
# TELEGRAM_TOKEN - токен от @BotFather
# JWT_TOKEN - токен для сервиса

# Запустить все сервисы
make docker-up

# Проверить логи
make docker-logs
```

### Локальная разработка

```bash
# Установить зависимости
make install

# Запустить сервисы
make dev

# Для остановки просто нажмите Ctrl+C
```

## 📋 Сервисы

### Telegram Bot
- **Порт**: В контейнере
- **Технология**: aiogram 3.0
- **Функции**:
  - /start - начало работы
  - /my_tasks - мои задачи
  - /assigned - назначенные мне
  - /new_task - создать задачу
  - /done <id> - отметить выполненной

### Task Service (Rust)
- **Порт**: 8000
- **Endpoints**:
  - GET /tasks/owner/{owner_id}
  - GET /tasks/assignee/{assignee_id}
  - POST /task
  - PATCH /task
  - PATCH /done/{task_id}

### Event Consumer
- **Подписывается на**: RabbitMQ events
- **Функции**:
  - Обработка task.created
  - Обработка task.updated
  - Обработка task.deleted
  - Локальное кэширование

### RabbitMQ
- **Порт**: 5672 (AMQP), 15672 (Management UI)
- **URL**: http://localhost:15672
- **Credentials**: guest/guest

### PostgreSQL
- **Порт**: 5432
- **User**: taskuser
- **Password**: taskpass
- **Database**: task_manager

## 🔧 Переменные окружения

```env
# Telegram
TELEGRAM_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# JWT
JWT_TOKEN=your_secret_jwt_token

# URLs
TASK_SERVICE_URL=http://localhost:8000
RABBITMQ_URL=amqp://guest:guest@localhost/

# Debug
DEBUG=True
```

## 📦 Структура проекта

```
task_manager/
├── telegram_bot/
│   ├── api_client.py          # HTTP клиент для Task Service
│   ├── handlers.py            # Обработчики команд
│   ├── keyboards.py           # Кнопки и клавиатуры
│   ├── schemas.py             # Pydantic модели
│   ├── config.py              # Конфигурация
│   ├── main.py                # Точка входа
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .gitignore
├── event_consumer/
│   ├── event_handler.py       # Обработчик RabbitMQ событий
│   ├── cache.py               # In-memory кэш
│   ├── config.py              # Конфигурация
│   ├── main.py                # Точка входа
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .gitignore
├── task_service/              # Rust сервис
│   ├── src/
│   │   ├── db.rs
│   │   ├── routes/
│   │   │   └── route.rs
│   │   └── ...
│   └── Cargo.toml
├── docker-compose.yml         # Оркестрация контейнеров
├── .env.example              # Пример переменных
├── .gitignore
├── Makefile                  # Команды для разработки
└── README.md
```

## 🐳 Docker команды

```bash
# Запустить все сервисы
docker-compose up -d

# Просмотреть логи
docker-compose logs -f

# Остановить сервисы
docker-compose down

# Пересобрать образы
docker-compose build --no-cache

# Запустить только RabbitMQ
docker-compose up -d rabbitmq

# Просмотреть логи конкретного сервиса
docker-compose logs -f telegram_bot
```

## 🧪 Тестирование

### Telegram Bot
1. Открыть Telegram
2. Найти вашего бота
3. Отправить /start
4. Использовать команды

### Task Service API
```bash
# Создать задачу
curl -X POST http://localhost:8000/task \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "Test Description",
    "status": "todo",
    "assignee_id": null
  }'

# Получить мои задачи
curl http://localhost:8000/tasks/owner/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## 🔐 Безопасность

- Используется JWT для аутентификации
- Переменные окружения в .env (не коммитятся)
- HTTPS рекомендуется для продакшена
- RabbitMQ защищен паролем

## 📊 Мониторинг

### RabbitMQ Management UI
- URL: http://localhost:15672
- Username: guest
- Password: guest

Здесь вы можете:
- Просмотреть очереди
- Просмотреть обмены
- Мониторить трафик
- Отладить сообщения

## 🛠️ Разработка

### Добавить новую команду в бота
1. Создать handler в `telegram_bot/handlers.py`
2. Добавить router в `telegram_bot/main.py`

### Добавить новый event
1. Обновить `task_service` для публикации события
2. Добавить handler в `event_consumer/event_handler.py`

### Расширить API
1. Добавить метод в `api_client.py`
2. Добавить handler в `telegram_bot/handlers.py`

## 📝 Лицензия

MIT License

## 👥 Контакты

- Task Service: http://localhost:8000
- RabbitMQ: http://localhost:15672
- PostgreSQL: localhost:5432
