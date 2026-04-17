import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock

import pytest


def install_aiogram_stub():
    aiogram_module = ModuleType("aiogram")
    aiogram_module.F = SimpleNamespace(text="text")
    aiogram_module.Router = lambda: SimpleNamespace(message=lambda *args, **kwargs: (lambda fn: fn))

    class DummyState:
        def __init__(self, *args, **kwargs):
            pass

    class DummyStatesGroup:
        pass

    filters_module = ModuleType("aiogram.filters.command")
    filters_module.Command = lambda *args, **kwargs: None

    fsm_context_module = ModuleType("aiogram.fsm.context")
    fsm_context_module.FSMContext = object

    fsm_state_module = ModuleType("aiogram.fsm.state")
    fsm_state_module.State = DummyState
    fsm_state_module.StatesGroup = DummyStatesGroup

    types_module = ModuleType("aiogram.types")
    types_module.Message = object
    types_module.KeyboardButton = lambda text: SimpleNamespace(text=text)
    types_module.ReplyKeyboardMarkup = lambda keyboard, resize_keyboard: SimpleNamespace(
        keyboard=keyboard,
        resize_keyboard=resize_keyboard,
    )

    sys.modules["aiogram"] = aiogram_module
    sys.modules["aiogram.filters.command"] = filters_module
    sys.modules["aiogram.fsm.context"] = fsm_context_module
    sys.modules["aiogram.fsm.state"] = fsm_state_module
    sys.modules["aiogram.types"] = types_module


install_aiogram_stub()

import handlers


class FakeState:
    def __init__(self, data=None):
        self.data = dict(data or {})
        self.current_state = None

    async def get_data(self):
        return dict(self.data)

    async def update_data(self, **kwargs):
        self.data.update(kwargs)

    async def set_state(self, state):
        self.current_state = state

    async def clear(self):
        self.data.clear()
        self.current_state = None


@pytest.mark.asyncio
async def test_require_auth_prompts_guest_when_session_missing():
    state = FakeState()
    message = SimpleNamespace(answer=AsyncMock())

    result = await handlers.require_auth(message, state)

    assert result is None
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_complete_login_registers_links_and_stores_session(monkeypatch):
    user_client = SimpleNamespace(
        register_user=AsyncMock(),
        login_user=AsyncMock(
            return_value={
                "access_token": "jwt-token",
                "user": {"id": 7, "email": "user@example.com"},
            }
        ),
        link_telegram=AsyncMock(),
    )
    monkeypatch.setattr(handlers, "get_user_client", lambda: user_client)

    state = FakeState()
    message = SimpleNamespace(
        from_user=SimpleNamespace(id=321),
        answer=AsyncMock(),
    )

    await handlers.complete_login(
        message=message,
        state=state,
        email="user@example.com",
        password="secret123",
        is_registration=True,
    )

    user_client.register_user.assert_awaited_once_with(
        email="user@example.com",
        password="secret123",
        telegram_id=321,
    )
    user_client.link_telegram.assert_awaited_once_with(
        token="jwt-token",
        telegram_id=321,
    )
    assert state.data["auth_token"] == "jwt-token"
    assert state.data["auth_user_id"] == 7
    assert state.data["auth_email"] == "user@example.com"
    message.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_process_deadline_creates_task_and_preserves_auth_session(monkeypatch):
    task_client = SimpleNamespace(
        create_task=AsyncMock(return_value={"id": 15}),
    )
    monkeypatch.setattr(handlers, "get_task_client", lambda: task_client)

    state = FakeState(
        {
            "auth_token": "jwt-token",
            "auth_user_id": 9,
            "auth_email": "owner@example.com",
            "task_title": "Prepare release",
            "task_description": "Cut release candidate",
            "task_assignee_id": 11,
        }
    )
    message = SimpleNamespace(text="/skip", answer=AsyncMock())

    await handlers.process_deadline(message, state)

    task_client.create_task.assert_awaited_once()
    args = task_client.create_task.await_args.args
    assert args[0] == "jwt-token"
    assert args[1].title == "Prepare release"
    assert args[1].assignee_id == 11
    assert args[1].deadline is None
    assert state.data["auth_user_id"] == 9
    message.answer.assert_awaited_once()
