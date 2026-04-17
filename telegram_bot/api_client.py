import logging
from typing import Any, Optional

import httpx

from config import TASK_SERVICE_URL, USER_SERVICE_URL
from schemas import TaskCreateRequest, TaskResponse, TaskUpdateRequest

logger = logging.getLogger(__name__)


class ServiceApiError(Exception):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class BaseApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    async def _request(
        self,
        method: str,
        path: str,
        *,
        token: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        headers = kwargs.pop("headers", {})
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method, f"{self.base_url}{path}", headers=headers, **kwargs
                )
            except httpx.HTTPError as exc:
                logger.exception("HTTP request failed: %s %s", method, path)
                raise ServiceApiError(503, "Service is unavailable") from exc

        if response.is_error:
            detail = "Request failed"
            try:
                payload = response.json()
                detail = payload.get("detail") or payload.get("error") or detail
            except ValueError:
                if response.text:
                    detail = response.text

            raise ServiceApiError(response.status_code, detail)

        if not response.content:
            return None

        return response.json()


class UserServiceClient(BaseApiClient):
    def __init__(self):
        super().__init__(USER_SERVICE_URL)

    async def register_user(
        self, email: str, password: str, telegram_id: Optional[int] = None
    ) -> dict:
        payload = {"email": email, "password": password, "telegram_id": telegram_id}
        return await self._request("POST", "/users/register", json=payload)

    async def login_user(self, email: str, password: str) -> dict:
        return await self._request(
            "POST",
            "/users/login",
            data={"username": email, "password": password},
        )

    async def link_telegram(self, token: str, telegram_id: int) -> dict:
        return await self._request(
            "POST",
            "/users/telegram/link",
            token=token,
            json={"telegram_id": telegram_id},
        )

    async def find_user_by_email(self, email: str) -> dict:
        return await self._request("GET", "/users/by-email", params={"email": email})


class TaskServiceClient(BaseApiClient):
    def __init__(self):
        super().__init__(TASK_SERVICE_URL)

    async def get_tasks_by_owner(
        self, token: str, owner_id: int
    ) -> list[TaskResponse]:
        return await self._request("GET", f"/tasks/owner/{owner_id}", token=token)

    async def get_tasks_by_assignee(
        self, token: str, assignee_id: int
    ) -> list[TaskResponse]:
        return await self._request(
            "GET", f"/tasks/assignee/{assignee_id}", token=token
        )

    async def create_task(
        self, token: str, task: TaskCreateRequest
    ) -> Optional[TaskResponse]:
        payload = task.model_dump(exclude_none=True)
        payload["status"] = "pending"
        return await self._request("POST", "/task", token=token, json=payload)

    async def update_task(
        self, token: str, task: TaskUpdateRequest
    ) -> Optional[TaskResponse]:
        return await self._request(
            "PATCH",
            "/task",
            token=token,
            json=task.model_dump(exclude_none=True),
        )

    async def done_task(self, token: str, task_id: int) -> Optional[TaskResponse]:
        return await self._request("PATCH", f"/done/{task_id}", token=token)
