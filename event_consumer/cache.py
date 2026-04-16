from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TaskCache:
    def __init__(self):
        self._cache: Dict[int, dict] = {}
    
    def set_task(self, task_id: int, task_data: dict):
        """Сохранить или обновить задачу в кэше"""
        self._cache[task_id] = task_data
        logger.debug(f"💾 Cached task {task_id}")
    
    def get_task(self, task_id: int) -> Optional[dict]:
        """Получить задачу из кэша"""
        return self._cache.get(task_id)
    
    def get_tasks_by_owner(self, owner_id: int):
        """Получить все задачи владельца из кэша"""
        return [task for task in self._cache.values() if task.get("owner_id") == owner_id]
    
    def get_tasks_by_assignee(self, assignee_id: int):
        """Получить все задачи исполнителя из кэша"""
        return [task for task in self._cache.values() if task.get("assignee_id") == assignee_id]
    
    def delete_task(self, task_id: int):
        """Удалить задачу из кэша"""
        if task_id in self._cache:
            del self._cache[task_id]
            logger.debug(f"🗑 Deleted task {task_id} from cache")
    
    def clear(self):
        """Очистить весь кэш"""
        self._cache.clear()
        logger.info("🧹 Cache cleared")
