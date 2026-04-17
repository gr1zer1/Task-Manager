from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class UserCache:
    def __init__(self):
        self._cache: Dict[int, dict] = {}

    def set_user(self, user_id: int, user_data: dict):
        self._cache[user_id] = user_data
        logger.debug("Cached user %s", user_id)

    def get_user(self, user_id: int) -> Optional[dict]:
        return self._cache.get(user_id)

    def delete_user(self, user_id: int):
        if user_id in self._cache:
            del self._cache[user_id]

    def clear(self):
        self._cache.clear()
        logger.info("User cache cleared")
