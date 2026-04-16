import asyncio
import logging
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from config import TELEGRAM_TOKEN, DEBUG
from handlers import router
from api_client import TaskServiceClient, AuthServiceClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Глобальная переменная для клиента
task_client: TaskServiceClient = None


async def initialize_auth() -> TaskServiceClient:
    """Инициализировать аутентификацию и получить JWT токен"""
    logger.info("🔐 Initializing authentication...")
    
    auth_client = AuthServiceClient()
    
    # Попытаться зарегистрировать сервис
    await auth_client.register_service()
    
    # Получить JWT токен
    jwt_token = await auth_client.get_service_token()
    
    if not jwt_token:
        raise RuntimeError("❌ Failed to get JWT token from user_service")
    
    logger.info("✅ Authentication initialized successfully")
    return TaskServiceClient(jwt_token)


async def main():
    global task_client
    
    logger.info("🌟 Starting Telegram Bot")
    
    # Инициализировать аутентификацию
    task_client = await initialize_auth()
    
    storage = MemoryStorage()
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher(storage=storage)
    
    dp.include_router(router)
    
    # Передать клиент в router контекст
    router.ctx_data = {"task_client": task_client}
    
    logger.info("📡 Starting polling...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
