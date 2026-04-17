import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from api_client import ServiceApiError
from keyboards import get_guest_keyboard, get_main_keyboard
from schemas import TaskCreateRequest

logger = logging.getLogger(__name__)
router = Router()
task_client = None
user_client = None


def set_clients(task_service_client, user_service_client) -> None:
    global task_client, user_client

    task_client = task_service_client
    user_client = user_service_client


def get_task_client():
    return task_client


def get_user_client():
    return user_client


class AuthStates(StatesGroup):
    waiting_email = State()
    waiting_password = State()


class TaskStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_assignee = State()
    waiting_deadline = State()


async def get_auth_session(state: FSMContext) -> dict | None:
    data = await state.get_data()
    token = data.get("auth_token")
    user_id = data.get("auth_user_id")

    if not token or not user_id:
        return None

    return {
        "token": token,
        "user_id": user_id,
        "email": data.get("auth_email"),
    }


async def require_auth(message: Message, state: FSMContext) -> dict | None:
    session = await get_auth_session(state)
    if session:
        return session

    await message.answer(
        "Сначала войдите или зарегистрируйтесь.",
        reply_markup=get_guest_keyboard(),
    )
    return None


async def store_auth_session(state: FSMContext, session: dict) -> None:
    await state.update_data(
        auth_token=session["token"],
        auth_user_id=session["user_id"],
        auth_email=session.get("email"),
    )


def format_task(task: dict) -> str:
    deadline = task.get("deadline") or "не указан"
    assignee_id = task.get("assignee_id") or "не назначен"
    return (
        f"ID: {task['id']}\n"
        f"Название: {task['title']}\n"
        f"Статус: {task['status']}\n"
        f"Исполнитель: {assignee_id}\n"
        f"Дедлайн: {deadline}"
    )


def normalize_deadline(raw_value: str) -> str:
    value = raw_value.strip()

    for input_format in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            parsed = datetime.strptime(value, input_format)
            return parsed.strftime("%Y-%m-%dT%H:%M:%S")
        except ValueError:
            continue

    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
        return parsed.strftime("%Y-%m-%dT00:00:00")
    except ValueError as exc:
        raise ValueError(
            "Некорректный формат даты. Используйте YYYY-MM-DD HH:MM:SS, "
            "YYYY-MM-DD HH:MM или YYYY-MM-DD."
        ) from exc


async def complete_login(
    message: Message, state: FSMContext, email: str, password: str, is_registration: bool
) -> None:
    user_service = get_user_client()

    if is_registration:
        await user_service.register_user(
            email=email,
            password=password,
            telegram_id=message.from_user.id,
        )

    login_result = await user_service.login_user(email=email, password=password)
    await user_service.link_telegram(
        token=login_result["access_token"], telegram_id=message.from_user.id
    )

    await store_auth_session(
        state,
        {
            "token": login_result["access_token"],
            "user_id": login_result["user"]["id"],
            "email": login_result["user"]["email"],
        },
    )

    action_text = "Регистрация завершена" if is_registration else "Вход выполнен"
    await state.set_state(None)
    await state.update_data(auth_flow=None, pending_email=None)
    await message.answer(
        f"{action_text}.\n\nEmail: {login_result['user']['email']}",
        reply_markup=get_main_keyboard(),
    )


@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    session = await get_auth_session(state)

    if session:
        await message.answer(
            f"Вы вошли как {session['email']}.\nИспользуйте меню для работы с задачами.",
            reply_markup=get_main_keyboard(),
        )
        return

    await message.answer(
        "Бот работает с вашим аккаунтом Task Manager.\n"
        "Сначала зарегистрируйтесь или войдите по email и паролю.",
        reply_markup=get_guest_keyboard(),
    )


@router.message(F.text == "🆕 Регистрация")
@router.message(Command("register"))
async def register_start(message: Message, state: FSMContext):
    await state.update_data(auth_flow="register", pending_email=None)
    await state.set_state(AuthStates.waiting_email)
    await message.answer("Введите email для регистрации:")


@router.message(F.text == "🔐 Войти")
@router.message(Command("login"))
async def login_start(message: Message, state: FSMContext):
    await state.update_data(auth_flow="login", pending_email=None)
    await state.set_state(AuthStates.waiting_email)
    await message.answer("Введите email:")


@router.message(Command("logout"))
@router.message(F.text == "🚪 Выйти")
async def logout(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Сессия очищена.", reply_markup=get_guest_keyboard())


@router.message(AuthStates.waiting_email)
async def process_auth_email(message: Message, state: FSMContext):
    await state.update_data(pending_email=message.text.strip())
    await state.set_state(AuthStates.waiting_password)
    await message.answer("Введите пароль:")


@router.message(AuthStates.waiting_password)
async def process_auth_password(message: Message, state: FSMContext):
    data = await state.get_data()
    email = data.get("pending_email")
    auth_flow = data.get("auth_flow")

    try:
        await complete_login(
            message=message,
            state=state,
            email=email,
            password=message.text,
            is_registration=(auth_flow == "register"),
        )
    except ServiceApiError as exc:
        await state.set_state(AuthStates.waiting_email)
        await state.update_data(pending_email=None)
        await message.answer(
            f"Ошибка авторизации: {exc.detail}\nПопробуйте снова, начиная с email.",
            reply_markup=get_guest_keyboard(),
        )


@router.message(F.text == "📋 Мои задачи")
@router.message(Command("my_tasks"))
async def my_tasks(message: Message, state: FSMContext):
    session = await require_auth(message, state)
    if not session:
        return

    try:
        tasks = await get_task_client().get_tasks_by_owner(
            session["token"], session["user_id"]
        )
    except ServiceApiError as exc:
        await message.answer(f"Не удалось получить задачи: {exc.detail}")
        return

    if not tasks:
        await message.answer("У вас нет созданных задач.")
        return

    await message.answer("📋 Ваши задачи:\n\n" + "\n\n---\n\n".join(map(format_task, tasks)))


@router.message(F.text == "📝 Назначенные")
@router.message(Command("assigned"))
async def assigned_tasks(message: Message, state: FSMContext):
    session = await require_auth(message, state)
    if not session:
        return

    try:
        tasks = await get_task_client().get_tasks_by_assignee(
            session["token"], session["user_id"]
        )
    except ServiceApiError as exc:
        await message.answer(f"Не удалось получить задачи: {exc.detail}")
        return

    if not tasks:
        await message.answer("На вас пока ничего не назначено.")
        return

    await message.answer("📝 Назначенные задачи:\n\n" + "\n\n---\n\n".join(map(format_task, tasks)))


@router.message(F.text == "➕ Новая задача")
@router.message(Command("new_task"))
async def new_task(message: Message, state: FSMContext):
    session = await require_auth(message, state)
    if not session:
        return

    await state.set_state(TaskStates.waiting_title)
    await message.answer("Введите название задачи:")


@router.message(TaskStates.waiting_title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(task_title=message.text.strip())
    await state.set_state(TaskStates.waiting_description)
    await message.answer("Введите описание или отправьте /skip:")


@router.message(TaskStates.waiting_description)
async def process_description(message: Message, state: FSMContext):
    if message.text != "/skip":
        await state.update_data(task_description=message.text.strip())

    await state.set_state(TaskStates.waiting_assignee)
    await message.answer("Введите email исполнителя или /skip:")


@router.message(TaskStates.waiting_assignee)
async def process_assignee(message: Message, state: FSMContext):
    if message.text != "/skip":
        try:
            assignee = await get_user_client().find_user_by_email(message.text.strip())
        except ServiceApiError as exc:
            await message.answer(f"Не удалось найти пользователя: {exc.detail}")
            return

        await state.update_data(
            task_assignee_id=assignee["id"],
            task_assignee_email=assignee["email"],
        )

    await state.set_state(TaskStates.waiting_deadline)
    await message.answer(
        "Введите дедлайн в формате YYYY-MM-DD HH:MM:SS, YYYY-MM-DD HH:MM "
        "или YYYY-MM-DD. Можно также /skip."
    )


@router.message(TaskStates.waiting_deadline)
async def process_deadline(message: Message, state: FSMContext):
    session = await require_auth(message, state)
    if not session:
        return

    data = await state.get_data()
    if message.text == "/skip":
        deadline = None
    else:
        try:
            deadline = normalize_deadline(message.text)
        except ValueError as exc:
            await message.answer(str(exc))
            return

    task_request = TaskCreateRequest(
        title=data["task_title"],
        description=data.get("task_description"),
        assignee_id=data.get("task_assignee_id"),
        deadline=deadline,
    )

    try:
        created_task = await get_task_client().create_task(session["token"], task_request)
    except ServiceApiError as exc:
        await message.answer(f"Не удалось создать задачу: {exc.detail}")
        await store_auth_session(state, session)
        return

    await state.clear()
    await store_auth_session(state, session)
    await message.answer(
        f"Задача создана.\nID: {created_task['id']}",
        reply_markup=get_main_keyboard(),
    )


@router.message(F.text == "✅ Отметить выполненной")
async def mark_done_hint(message: Message):
    await message.answer("Используйте команду `/done <task_id>`.", parse_mode="Markdown")


@router.message(Command("done"))
async def mark_done(message: Message, state: FSMContext):
    session = await require_auth(message, state)
    if not session:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("Используйте: /done <task_id>")
        return

    try:
        task_id = int(args[1])
    except ValueError:
        await message.answer("ID задачи должен быть числом.")
        return

    try:
        await get_task_client().done_task(session["token"], task_id)
    except ServiceApiError as exc:
        await message.answer(f"Не удалось обновить задачу: {exc.detail}")
        return

    await message.answer(f"Задача #{task_id} отмечена как выполненная.")


@router.message(F.text == "❓ Помощь")
@router.message(Command("help"))
async def help_command(message: Message, state: FSMContext):
    session = await get_auth_session(state)
    if session:
        text = (
            "Команды:\n"
            "/my_tasks - мои задачи\n"
            "/assigned - назначенные мне\n"
            "/new_task - создать задачу\n"
            "/done <id> - отметить выполненной\n"
            "/logout - выйти"
        )
        keyboard = get_main_keyboard()
    else:
        text = (
            "Сначала войдите в существующий аккаунт или зарегистрируйте новый.\n"
            "Команды:\n"
            "/login - вход\n"
            "/register - регистрация"
        )
        keyboard = get_guest_keyboard()

    await message.answer(text, reply_markup=keyboard)
