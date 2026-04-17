import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from api_client import TaskServiceClient, UserServiceClient
from config import TELEGRAM_TOKEN
from handlers import router, set_clients

task_client: TaskServiceClient | None = None
user_client: UserServiceClient | None = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    global task_client, user_client

    logger.info("Starting Telegram Bot")

    task_client = TaskServiceClient()
    user_client = UserServiceClient()
    set_clients(task_client, user_client)

    storage = MemoryStorage()
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
