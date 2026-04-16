# JWT Authentication Flow

## Описание

Вместо того, чтобы хранить JWT токен в переменной окружения, бот теперь:
1. **Регистрируется** как сервис в user_service
2. **Получает JWT токен** от user_service при запуске
3. **Использует токен** для всех запросов к task_service

## Архитектура

```
┌─────────────────┐
│  Telegram Bot   │
│   (Python)      │
└────────┬────────┘
         │
         ├─── POST /users/register ──────┐
         │                               │
         │    ┌─────────────────────┐   │
         │    │  User Service       │   │
         │    │  (Python)           │◄──┘
         │    └─────────────────────┘
         │
         └─── POST /users/login ────────┐
                                        │
              ┌────────────────────┐   │
              │ Return JWT Token   │◄──┘
              └────────────────────┘
                     │
                     ▼
              (Store in memory)
                     │
                     ▼
         ┌───────────────────────┐
         │  Telegram Bot         │
         │  (with JWT token)     │
         └───────────┬───────────┘
                     │
                     ├─── GET /tasks/owner/{id}
                     ├─── GET /tasks/assignee/{id}
                     ├─── POST /task
                     └─── PATCH /done/{id}
                     │
                     ▼
            ┌─────────────────────┐
            │  Task Service       │
            │  (Rust)             │
            └─────────────────────┘
```

## Файлы, которые были изменены

### 1. **config.py** 
Вместо `JWT_TOKEN` из env:
```python
# Старый способ
JWT_TOKEN = os.getenv("JWT_TOKEN")

# Новый способ
SERVICE_EMAIL = os.getenv("SERVICE_EMAIL", "bot@service.local")
SERVICE_PASSWORD = os.getenv("SERVICE_PASSWORD")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
```

### 2. **api_client.py**
Добавлены два класса:

#### `TaskServiceClient`
- Теперь принимает JWT токен в конструкторе
- Может обновлять токен через метод `update_token()`

```python
client = TaskServiceClient(jwt_token)
client.update_token(new_token)
```

#### `AuthServiceClient` (новый)
- Регистрирует сервис в user_service
- Получает JWT токен через login endpoint

```python
auth_client = AuthServiceClient()
await auth_client.register_service()
jwt_token = await auth_client.get_service_token()
```

### 3. **main.py**
Добавлена инициализация:
```python
async def initialize_auth() -> TaskServiceClient:
    """Инициализировать аутентификацию и получить JWT токен"""
    auth_client = AuthServiceClient()
    await auth_client.register_service()
    jwt_token = await auth_client.get_service_token()
    return TaskServiceClient(jwt_token)

async def main():
    global task_client
    task_client = await initialize_auth()  # ✅ Получить токен перед запуском
    # ... rest of setup
```

### 4. **handlers.py**
Все обработчики теперь используют глобальный `task_client`:
```python
def get_task_client():
    from main import task_client
    return task_client
```

### 5. **.env.example**
Новые переменные:
```env
SERVICE_EMAIL=bot@service.local
SERVICE_PASSWORD=your_service_password_here
USER_SERVICE_URL=http://localhost:8001
```

## Процесс аутентификации

### Шаг 1: Регистрация
```bash
POST /users/register
Content-Type: application/json

{
  "email": "bot@service.local",
  "password": "service_password"
}

Response: 201 Created или 409 Conflict (уже зарегистрирован)
```

### Шаг 2: Получение JWT
```bash
POST /users/login
Content-Type: application/x-www-form-urlencoded

username=bot@service.local&password=service_password

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { ... }
}
```

### Шаг 3: Использование JWT
```bash
GET /tasks/owner/1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## Преимущества

✅ **Безопасность**: Токен не хранится в .env  
✅ **Динамичность**: Токен можно обновлять без перезапуска  
✅ **Масштабируемость**: Поддержка нескольких сервисов-клиентов  
✅ **Аудит**: Все операции привязаны к service account  

## Обработка ошибок

Если бот не может получить JWT:
```
❌ Failed to get JWT token from user_service
RuntimeError raised during startup
```

**Решение:**
1. Проверить, запущен ли user_service
2. Проверить SERVICE_EMAIL и SERVICE_PASSWORD в .env
3. Проверить USER_SERVICE_URL

## Логирование

Весь процесс логируется:
```
🔐 Initializing authentication...
✅ Service registered
✅ Got JWT token from user_service
✅ Authentication initialized successfully
📡 Starting polling...
```

## Docker Compose

В docker-compose.yml telegram_bot теперь зависит от api (user_service):
```yaml
telegram_bot:
  depends_on:
    api:
      condition: service_healthy
```

Это гарантирует, что user_service будет запущен перед ботом.
