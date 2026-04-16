import logging
from typing import List, Optional

import httpx
from config import SERVICE_EMAIL, SERVICE_PASSWORD, TASK_SERVICE_URL, USER_SERVICE_URL
from schemas import TaskCreateRequest, TaskResponse, TaskUpdateRequest

logger = logging.getLogger(__name__)


class TaskServiceClient:
    def __init__(self, jwt_token: str):
        self.base_url = TASK_SERVICE_URL
        self.jwt_token = jwt_token
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json",
        }

    def update_token(self, jwt_token: str):
        """Обновить JWT токен"""
        self.jwt_token = jwt_token
        self.headers["Authorization"] = f"Bearer {jwt_token}"
        logger.info("JWT token updated")

    async def get_tasks_by_owner(self, owner_id: int) -> Optional[List[TaskResponse]]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/tasks/owner/{owner_id}", headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error fetching tasks: {e}")
                return None

    async def get_tasks_by_assignee(
        self, assignee_id: int
    ) -> Optional[List[TaskResponse]]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/tasks/assignee/{assignee_id}",
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error fetching tasks: {e}")
                return None

    async def create_task(
        self, task: TaskCreateRequest, user_id: int
    ) -> Optional[TaskResponse]:
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "title": task.title,
                    "description": task.description,
                    "status": "todo",
                    "owner_id": user_id,
                    "assignee_id": task.assignee_id,
                    "deadline": task.deadline,
                }
                response = await client.post(
                    f"{self.base_url}/task", json=payload, headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error creating task: {e}")
                return None

    async def update_task(self, task: TaskUpdateRequest) -> Optional[TaskResponse]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"{self.base_url}/task",
                    json=task.dict(exclude_none=True),
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error updating task: {e}")
                return None

    async def done_task(self, task_id: int) -> Optional[TaskResponse]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"{self.base_url}/done/{task_id}", headers=self.headers
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                print(f"Error marking task as done: {e}")
                return None


class AuthServiceClient:
    """Клиент для получения JWT от user_service"""

    def __init__(self):
        self.base_url = USER_SERVICE_URL

    async def get_service_token(self) -> Optional[str]:
        """Получить JWT токен для сервиса"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/users/login",
                    data={"username": SERVICE_EMAIL, "password": SERVICE_PASSWORD},
                )
                if response.status_code != 200:
                    logger.error(
                        f"❌ Login failed: {response.status_code} - {response.text}"
                    )
                    return None
                response.raise_for_status()
                data = response.json()
                token = data.get("access_token")
                logger.info(f"✅ Got JWT token from user_service")
                return token
            except httpx.HTTPError as e:
                logger.error(f"❌ Error getting JWT token: {e}")
                return None

    async def register_service(self) -> bool:
        """Зарегистрировать сервис если не существует"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/users/register",
                    json={"email": SERVICE_EMAIL, "password": SERVICE_PASSWORD},
                )
                if response.status_code == 409:
                    logger.info("Service already registered")
                    return True
                if response.status_code != 200 and response.status_code != 201:
                    logger.error(
                        f"❌ Registration failed: {response.status_code} - {response.text}"
                    )
                    return False
                response.raise_for_status()
                logger.info(f"✅ Service registered")
                return True
            except httpx.HTTPError as e:
                logger.error(f"❌ Error registering service: {e}")
                return False
