import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest


aio_pika_stub = ModuleType("aio_pika")
aio_pika_stub.IncomingMessage = object
aio_pika_stub.ExchangeType = SimpleNamespace(TOPIC="topic")
aio_pika_stub.connect_robust = AsyncMock()
sys.modules["aio_pika"] = aio_pika_stub

import event_handler


class FakeProcessedMessage:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeIncomingMessage:
    def __init__(self, body: bytes, routing_key: str):
        self.body = body
        self.routing_key = routing_key

    def process(self):
        return FakeProcessedMessage()


def test_build_notification_for_created_event():
    message = event_handler.build_notification(
        "task.created",
        {"id": 42, "title": "Ship MVP", "status": "pending"},
    )

    assert "Новая задача #42" in message
    assert "Ship MVP" in message


@pytest.mark.asyncio
async def test_notify_task_participants_sends_only_to_linked_users(monkeypatch):
    monkeypatch.setattr(
        event_handler,
        "fetch_user",
        AsyncMock(
            side_effect=[
                {"id": 1, "telegram_id": 111},
                {"id": 2, "telegram_id": None},
            ]
        ),
    )
    send_message = AsyncMock()
    monkeypatch.setattr(event_handler, "send_telegram_message", send_message)

    await event_handler.notify_task_participants(
        "task.updated",
        {"id": 10, "title": "Fix auth", "status": "done", "owner_id": 1, "assignee_id": 2},
    )

    send_message.assert_awaited_once()
    assert send_message.await_args.args[0] == 111


@pytest.mark.asyncio
async def test_process_message_dispatches_notification(monkeypatch):
    notify = AsyncMock()
    monkeypatch.setattr(event_handler, "notify_task_participants", notify)

    message = FakeIncomingMessage(
        body=b'{"id": 5, "title": "Review PR", "owner_id": 1}',
        routing_key="task.created",
    )

    await event_handler.process_message(message)

    notify.assert_awaited_once_with(
        "task.created",
        {"id": 5, "title": "Review PR", "owner_id": 1},
    )
