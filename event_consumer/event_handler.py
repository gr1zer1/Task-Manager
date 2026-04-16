import aio_pika
import json
import logging
from config import RABBITMQ_URL, EXCHANGE_NAME, QUEUE_NAME, ROUTING_KEY
from cache import TaskCache

logger = logging.getLogger(__name__)
cache = TaskCache()


async def setup_rabbitmq():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        aio_pika.ExchangeType.TOPIC,
        durable=True
    )
    
    queue = await channel.declare_queue(
        QUEUE_NAME,
        durable=True
    )
    
    await queue.bind(exchange, ROUTING_KEY)
    
    return connection, channel, queue


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            body = json.loads(message.body)
            event_type = message.routing_key
            
            logger.info(f"📨 Received event: {event_type} - {body}")
            
            if event_type == "task.created":
                await handle_task_created(body)
            elif event_type == "task.updated":
                await handle_task_updated(body)
            elif event_type == "task.deleted":
                await handle_task_deleted(body)
        
        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")


async def handle_task_created(task_data: dict):
    """Обработка события создания задачи"""
    cache.set_task(task_data["id"], task_data)
    logger.info(f"✅ Task created: {task_data['id']}")


async def handle_task_updated(task_data: dict):
    """Обработка события обновления задачи"""
    cache.set_task(task_data["id"], task_data)
    logger.info(f"✅ Task updated: {task_data['id']}")


async def handle_task_deleted(task_data: dict):
    """Обработка события удаления задачи"""
    cache.delete_task(task_data["id"])
    logger.info(f"✅ Task deleted: {task_data['id']}")


async def start_consumer():
    connection, channel, queue = await setup_rabbitmq()
    logger.info("🚀 Event consumer started")
    
    await queue.consume(process_message)
    
    try:
        await asyncio.Event().wait()
    finally:
        await connection.close()
