import json
import logging

from aiogram import F, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from keyboards import get_main_keyboard

logger = logging.getLogger(__name__)

router = Router()

# Импортируем глобальный клиент из main
from main import task_client as get_task_client


def get_task_client():
    """Получить текущий task_client"""
    from main import task_client

    return task_client


class TaskStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_assignee = State()
    waiting_deadline = State()
    editing_task = State()


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в Task Manager Bot!\n\n"
        "Используйте команды ниже для управления задачами:",
        reply_markup=get_main_keyboard(),
    )


@router.message(F.text == "📋 Мои задачи")
@router.message(Command("my_tasks"))
async def my_tasks(message: Message):
    client = get_task_client()
    tasks = await client.get_tasks_by_owner(message.from_user.id)

    if not tasks:
        await message.answer("📭 У вас нет задач")
        return

    response = "📋 Ваши задачи:\n\n"
    for task in tasks:
        response += f"ID: {task['id']}\n"
        response += f"Название: {task['title']}\n"
        response += f"Статус: {task['status']}\n"
        response += f"---\n"

    await message.answer(response)


@router.message(F.text == "📝 Назначенные")
@router.message(Command("assigned"))
async def assigned_tasks(message: Message):
    client = get_task_client()
    tasks = await client.get_tasks_by_assignee(message.from_user.id)

    if not tasks:
        await message.answer("📭 Вам не назначены задачи")
        return

    response = "📝 Назначенные вам задачи:\n\n"
    for task in tasks:
        response += f"ID: {task['id']}\n"
        response += f"Название: {task['title']}\n"
        response += f"Автор: {task['owner_id']}\n"
        response += f"Статус: {task['status']}\n"
        response += f"---\n"

    await message.answer(response)


@router.message(F.text == "➕ Новая задача")
@router.message(Command("new_task"))
async def new_task(message: Message, state: FSMContext):
    await state.set_state(TaskStates.waiting_title)
    await message.answer("📝 Введите название задачи:")


@router.message(TaskStates.waiting_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(TaskStates.waiting_description)
    await message.answer("📄 Введите описание (или отправьте /skip):")


@router.message(TaskStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    if message.text != "/skip":
        await state.update_data(description=message.text)
    await state.set_state(TaskStates.waiting_assignee)
    await message.answer("👤 Введите ID исполнителя (или /skip если нет):")


@router.message(TaskStates.waiting_assignee)
async def process_assignee(message: Message, state: FSMContext):
    if message.text != "/skip":
        try:
            assignee_id = int(message.text)
            await state.update_data(assignee_id=assignee_id)
        except ValueError:
            await message.answer("❌ Введите корректный ID")
            return

    await state.set_state(TaskStates.waiting_deadline)
    await message.answer("📅 Введите дедлайн (YYYY-MM-DD или /skip):")


@router.message(TaskStates.waiting_deadline)
async def process_deadline(message: Message, state: FSMContext):
    data = await state.get_data()
    client = get_task_client()

    if message.text != "/skip":
        deadline = message.text
    else:
        deadline = None

    from schemas import TaskCreateRequest

    task_request = TaskCreateRequest(
        title=data["title"],
        description=data.get("description"),
        assignee_id=data.get("assignee_id"),
        deadline=deadline,
    )

    created_task = await client.create_task(task_request, message.from_user.id)

    if created_task:
        await message.answer(f"✅ Задача создана!\nID: {created_task['id']}")
    else:
        await message.answer("❌ Ошибка при создании задачи")

    await state.clear()


@router.message(F.text == "❓ Помощь")
@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "❓ Справка по командам:\n\n"
        "📋 /my_tasks - Посмотреть мои созданные задачи\n"
        "📝 /assigned - Посмотреть назначенные мне задачи\n"
        "➕ /new_task - Создать новую задачу\n"
        "✅ /done <id> - Отметить задачу как выполненную\n\n"
        "Вы также можете использовать кнопки на клавиатуре!"
    )


@router.message(F.text == "✅ Отметить выполненной")
async def mark_done_hint(message: Message):
    await message.answer(
        "📌 Чтобы отметить задачу как выполненную, отправьте команду:\n`/done <task_id>`\n\nГде `<task_id>` - это номер задачи из списка.",
        parse_mode="Markdown",
    )


@router.message(Command("done"))
async def mark_done(message: Message):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("📌 Используйте: /done <task_id>")
        return

    try:
        task_id = int(args[1])
        client = get_task_client()
        result = await client.done_task(task_id)
        if result:
            await message.answer(f"✅ Задача #{task_id} отмечена как выполненная")
        else:
            await message.answer("❌ Ошибка при обновлении")
    except ValueError:
        await message.answer("❌ Введите корректный ID")
