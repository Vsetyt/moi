import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class NotificationScheduler:
    def __init__(self, bot, db_manager):
        self.bot = bot
        self.db_manager = db_manager
        self.scheduled_notifications: Dict[int, List[Dict]] = {}

    async def schedule_notification(self, user_id: int, message: str, delay: timedelta):
        if user_id not in self.scheduled_notifications:
            self.scheduled_notifications[user_id] = []

        scheduled_time = datetime.now() + delay
        self.scheduled_notifications[user_id].append({
            'message': message,
            'scheduled_time': scheduled_time
        })
        logger.info(f"Scheduled notification for user {user_id} at {scheduled_time}")

    async def run(self):
        while True:
            await self.check_notifications()
            await asyncio.sleep(60)  # Проверяем каждую минуту

    async def check_notifications(self):
        now = datetime.now()
        for user_id, notifications in self.scheduled_notifications.items():
            for notification in notifications[:]:
                if now >= notification['scheduled_time']:
                    await self.send_notification(user_id, notification['message'])
                    notifications.remove(notification)

    async def send_notification(self, user_id: int, message: str):
        try:
            await self.bot.send_message(chat_id=user_id, text=message)
            logger.info(f"Sent scheduled notification to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send scheduled notification to user {user_id}: {str(e)}")

    def clear_notifications(self, user_id: int):
        if user_id in self.scheduled_notifications:
            self.scheduled_notifications[user_id].clear()
            logger.info(f"Cleared all scheduled notifications for user {user_id}")