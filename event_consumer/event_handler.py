import asyncio
import json
import logging

import aio_pika
import httpx

from cache import UserCache
from config import (
    EXCHANGE_NAME,
    QUEUE_NAME,
    RABBITMQ_URL,
    ROUTING_KEY,
    TELEGRAM_TOKEN,
    USER_SERVICE_URL,
)

logger = logging.getLogger(__name__)
user_cache = UserCache()


async def setup_rabbitmq():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()

    exchange = await channel.declare_exchange(
        EXCHANGE_NAME,
        aio_pika.ExchangeType.TOPIC,
        durable=True,
    )

    queue = await channel.declare_queue(
        QUEUE_NAME,
        durable=True,
    )

    await queue.bind(exchange, ROUTING_KEY)

    return connection, queue


async def fetch_user(user_id: int) -> dict | None:
    cached_user = user_cache.get_user(user_id)
    if cached_user:
        return cached_user

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
        except httpx.HTTPError as exc:
            logger.error("Failed to fetch user %s: %s", user_id, exc)
            return None

    if response.status_code != 200:
        logger.warning("User %s was not found in user_service", user_id)
        return None

    user_data = response.json()
    user_cache.set_user(user_id, user_data)
    return user_data


async def send_telegram_message(telegram_id: int, text: str):
    if not TELEGRAM_TOKEN:
        logger.warning("TELEGRAM_TOKEN is not configured for event_consumer")
        return

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={"chat_id": telegram_id, "text": text},
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error("Failed to send Telegram message to %s: %s", telegram_id, exc)


def build_notification(event_type: str, task_data: dict) -> str:
    title = task_data.get("title", "Без названия")
    status = task_data.get("status", "unknown")
    task_id = task_data.get("id")

    if event_type == "task.created":
        return f"Новая задача #{task_id}: {title}\nСтатус: {status}"
    if event_type == "task.updated":
        return f"Задача #{task_id} обновлена: {title}\nСтатус: {status}"
    if event_type == "task.deleted":
        return f"Задача #{task_id} удалена: {title}"

    return f"Событие по задаче #{task_id}: {title}"


async def notify_task_participants(event_type: str, task_data: dict):
    recipient_ids = {
        user_id
        for user_id in [task_data.get("owner_id"), task_data.get("assignee_id")]
        if user_id is not None
    }

    if not recipient_ids:
        return

    text = build_notification(event_type, task_data)

    for user_id in recipient_ids:
        user_data = await fetch_user(user_id)
        if not user_data:
            continue

        telegram_id = user_data.get("telegram_id")
        if not telegram_id:
            logger.info("User %s has no linked Telegram account", user_id)
            continue

        await send_telegram_message(telegram_id, text)


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        try:
            body = json.loads(message.body)
            event_type = message.routing_key
            logger.info("Received event %s for task %s", event_type, body.get("id"))
            await notify_task_participants(event_type, body)
        except Exception as exc:
            logger.exception("Error processing message: %s", exc)


async def start_consumer():
    connection, queue = await setup_rabbitmq()
    logger.info("Event consumer started")

    await queue.consume(process_message)

    try:
        await asyncio.Event().wait()
    finally:
        await connection.close()
