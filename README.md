# Task Manager

Task Manager is a small distributed task platform built around a Telegram-first workflow.  
The repository combines a Python bot, a Rust task API, a Python user service, RabbitMQ-driven notifications, and Docker-based local orchestration.

## Overview

- Telegram bot with registration and login by email/password
- JWT-based authorization between services
- Task creation, assignment, listing, and completion
- RabbitMQ events for task lifecycle changes
- Telegram notifications for task participants
- Docker Compose environment for local development

## Architecture

```text
Telegram Bot (aiogram)
    |
    | HTTP
    v
User Service (FastAPI) <----> PostgreSQL
    |
    | JWT
    v
Task Service (Axum + Rust) <----> PostgreSQL
    |
    | task.*
    v
RabbitMQ
    |
    v
Event Consumer (Python)
    |
    v
Telegram notifications
```

## Services

### `telegram_bot`

The user-facing entrypoint.

- registration and login by email/password
- task creation from chat
- owner and assignee task views
- task completion flow

### `user_service`

Authentication and identity service.

- user registration
- login and JWT issuing
- Telegram account linking
- user lookup by email or Telegram ID

### `task_service`

Core task API written in Rust.

- list tasks by owner
- list tasks by assignee
- create task
- update task
- mark task as done
- publish task events to RabbitMQ

### `event_consumer`

Background worker for task notifications.

- subscribes to `task.*`
- loads task participants from `user_service`
- sends Telegram notifications

## Stack

- Python 3.12
- FastAPI
- aiogram
- Rust + Axum
- PostgreSQL
- RabbitMQ
- Docker Compose

## Local Run

### Prerequisites

- Docker
- Docker Compose
- Telegram bot token from `@BotFather`

### Start

```bash
docker compose up -d --build
```

### Stop

```bash
docker compose down
```

### Check status

```bash
docker compose ps
docker compose logs -f telegram_bot
docker compose logs -f api
docker compose logs -f task_api
```

## Main Endpoints

### User Service

- `POST /users/register`
- `POST /users/login`
- `POST /users/telegram/link`
- `GET /users/by-email`
- `GET /users/telegram/{telegram_id}`
- `GET /users/{user_id}`
- `GET /health`

### Task Service

- `GET /tasks/owner/{owner_id}`
- `GET /tasks/assignee/{assignee_id}`
- `POST /task`
- `PATCH /task`
- `PATCH /done/{task_id}`

## Environment

Typical variables used by the stack:

```env
TELEGRAM_TOKEN=your_bot_token

USER_SERVICE_URL=http://api:8001
TASK_SERVICE_URL=http://task_api:8002
RABBITMQ_URL=amqp://guest:guest@rabbitmq/

DATABASE_URL=postgresql+asyncpg://...
TASK_DATABASE_URL=postgres://...
JWT_SECRET_KEY=your_secret

POSTGRES_USER=...
POSTGRES_PASSWORD=...
POSTGRES_DB=...

TASK_POSTGRES_USER=...
TASK_POSTGRES_PASSWORD=...
TASK_POSTGRES_DB=...

RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
```

## Testing

### Python services

```bash
cd user_service && pytest -q
cd telegram_bot && pytest -q
cd event_consumer && pytest -q
```

### Rust service

```bash
cd task_service && cargo test
```

## Repository Layout

```text
task_manager/
├── telegram_bot/
├── user_service/
├── task_service/
├── event_consumer/
├── docker-compose.yml
└── README.md
```

## Notes

- `telegram_bot` stores user auth state in bot FSM storage
- access tokens are used directly; refresh flow is not implemented in the bot yet
- task events are published after successful task mutations
- RabbitMQ Management UI is available on `http://localhost:15672`
