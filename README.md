# Task Manager API

Переделанный Task Manager с использованием архитектуры из url_short analytics сервиса.

## Архитектурные улучшения

### 1. **Структура проекта**
```
task_manager/
├── core/                    # Ядро приложения
│   ├── config.py           # Единая конфигурация с Pydantic Settings
│   ├── db.py               # DBHelper класс для управления БД
│   ├── auth.py             # JWT аутентификация (сохранено)
│   ├── utility.py          # Утилиты (хеширование пароля)
│   ├── models/
│   │   ├── base.py         # Base класс с автоматическим __tablename__
│   │   └── __init__.py     # User и Task модели
│   └── __init__.py
├── users/                   # User endpoints
│   ├── routes.py
│   ├── __init__.py
│   └── schemas.py          # Pydantic схемы (в tasks/)
├── tasks/                   # Task endpoints
│   ├── routes.py
│   ├── schemas.py          # Единая папка для всех Pydantic схем
│   └── __init__.py
├── main.py                 # Главное приложение с lifespan
├── alembic/                # Миграции БД
├── requirements.txt        # Очищенные зависимости
└── .env.example           # Пример переменных окружения
```

### 2. **Ключевые улучшения**

#### Config Management
- **Было**: Конфиг разбросан по разным файлам (auth.py, db.py)
- **Стало**: Единый `core/config.py` с Pydantic `BaseSettings` и `SettingsConfigDict`
- Все переменные окружения загружаются из `.env` файла

#### Database Layer
- **Было**: Простые функции `create_async_engine`, `SessionLocal`
- **Стало**: `DBHelper` класс с методами `dispose()` и `get_session()`
- Более гибкий и расширяемый подход
- Pool и overflow parameters для оптимизации

#### Models
- **Было**: Каждая модель со своим `__tablename__`
- **Стало**: `Base` класс с `@declared_attr` для автоматического `__tablename__`
- `TimestampMixin` для отслеживания `created_at` и `updated_at`
- Наследование моделями обоих для полной функциональности

#### Dependency Injection
- **Было**: `SessionDep = Annotated[AsyncSession, Depends(get_db)]`
- **Стало**: `SessionDep = Annotated[AsyncSession, Depends(db_helper.get_session)]`
- Консистентный паттерн со Annotated для типизации

#### Schemas
- **Было**: Рассредоточены по разным местам
- **Стало**: Единая папка `tasks/schemas.py` с `ConfigDict(from_attributes=True)`
- Все Pydantic модели в одном месте

#### Application Lifecycle
- **Было**: Нет управления жизненным циклом приложения
- **Стало**: `@asynccontextmanager` с `lifespan` для graceful shutdown БД
- Правильное закрытие соединений при остановке

### 3. **JWT Authentication (сохранено)**

JWT аутентификация оставлена без изменений в `core/auth.py`:
- `create_access_token()`
- `create_refresh_token()`
- `decode_token()`

Все настройки теперь берутся из `config`:
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`

## Запуск

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Подготовка окружения
```bash
cp .env.example .env
# Отредактируйте .env с вашими значениями
```

### 3. Миграции БД
```bash
alembic upgrade head
```

### 4. Запуск приложения
```bash
python main.py
```

Приложение запустится на `http://0.0.0.0:8000`

## API Endpoints

### Users
- `POST /users/register` - Регистрация
- `POST /users/login` - Вход
- `GET /users` - Все пользователи
- `GET /users/{user_id}` - Конкретный пользователь

### Tasks
- `POST /tasks` - Создание задачи
- `GET /tasks` - Задачи пользователя
- `GET /tasks/{task_id}` - Конкретная задача
- `PUT /tasks/{task_id}` - Обновление
- `DELETE /tasks/{task_id}` - Удаление

## Преимущества новой архитектуры

✅ **Масштабируемость** - Лучше организованная структура
✅ **Конфигуируемость** - Единая конфигурация через Pydantic
✅ **Реиспользуемость** - DBHelper можно использовать в других проектах
✅ **Типизация** - Лучшая типизация с Pydantic
✅ **Управление жизненным циклом** - Правильный startup/shutdown
✅ **Консистентность** - Паттерны соответствуют analytics сервису
