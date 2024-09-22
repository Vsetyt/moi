import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self, bot):
        self.bot = bot

    async def send_arbitrage_opportunity(self, user_id, opportunity):
        try:
            text = (f"🚀 Арбитражная возможность!\n\n"
                    f"Путь: {opportunity['path']}\n"
                    f"Прибыль: {opportunity['profit']:.2f}%\n"
                    f"Объем: {opportunity['volume']:.2f} USDT\n"
                    f"Волатильность: {opportunity['volatility']:.2f}%")
            
            keyboard = [
                [InlineKeyboardButton("Выполнить арбитраж", callback_data=f"execute_arbitrage_{opportunity['path']}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await self.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)
            logger.info(f"Sent arbitrage opportunity notification to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending arbitrage opportunity notification: {str(e)}")

    async def send_trade_execution(self, user_id, trade_info):
        try:
            text = (f"💹 Арбитражная сделка выполнена\n\n"
                    f"ID: {trade_info['id']}\n"
                    f"Путь: {trade_info['path']}\n"
                    f"Объем: {trade_info['volume']:.2f} USDT\n"
                    f"Ожидаемая прибыль: {trade_info['expected_profit']:.2f}%")
            
            await self.bot.send_message(chat_id=user_id, text=text)
            logger.info(f"Sent trade execution notification to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending trade execution notification: {str(e)}")

    async def send_trade_closure(self, user_id, trade_info):
        try:
            text = (f"🏁 Арбитражная сделка закрыта\n\n"
                    f"ID: {trade_info['id']}\n"
                    f"Путь: {trade_info['path']}\n"
                    f"Фактическая прибыль: {trade_info['actual_profit']:.2f}%")
            
            await self.bot.send_message(chat_id=user_id, text=text)
            logger.info(f"Sent trade closure notification to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending trade closure notification: {str(e)}")

    async def send_error_notification(self, user_id, error_message):
        try:
            text = f"❗ Ошибка: {error_message}"
            await self.bot.send_message(chat_id=user_id, text=text)
            logger.info(f"Sent error notification to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending error notification: {str(e)}")