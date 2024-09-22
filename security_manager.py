import hashlib
import secrets
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        return hashlib.sha256((password + salt).encode()).hexdigest() + ':' + salt

    def verify_password(self, stored_password: str, provided_password: str) -> bool:
        stored_hash, salt = stored_password.split(':')
        return stored_hash == hashlib.sha256((provided_password + salt).encode()).hexdigest()

    def generate_api_key(self) -> str:
        return secrets.token_urlsafe(32)

    def store_user_credentials(self, user_id: int, password: str):
        hashed_password = self.hash_password(password)
        self.db_manager.update_user_credentials(user_id, hashed_password)

    def verify_user_credentials(self, user_id: int, password: str) -> bool:
        stored_password = self.db_manager.get_user_credentials(user_id)
        if stored_password:
            return self.verify_password(stored_password, password)
        return False

    def generate_and_store_api_key(self, user_id: int) -> str:
        api_key = self.generate_api_key()
        self.db_manager.update_user_api_key(user_id, api_key)
        return api_key

    def verify_api_key(self, api_key: str) -> int:
        return self.db_manager.get_user_id_by_api_key(api_key)

    def log_security_event(self, event_type: str, user_id: int, details: Dict):
        logger.warning(f"Security event: {event_type}, User ID: {user_id}, Details: {details}")
        # Здесь можно добавить логику для сохранения событий безопасности в базе данных или отправки уведомлений