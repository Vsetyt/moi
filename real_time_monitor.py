import asyncio
from typing import Dict, List
import logging
import time

logger = logging.getLogger(__name__)

class RealTimeMonitor:
    def __init__(self, update_interval: int = 60):
        self.update_interval = update_interval
        self.performance_metrics = {}
        self.alerts = []

    async def start_monitoring(self, arbitrage_bot):
        while True:
            await self.update_metrics(arbitrage_bot)
            await self.check_alerts()
            await asyncio.sleep(self.update_interval)

    async def update_metrics(self, arbitrage_bot):
        self.performance_metrics = {
            'balance': await arbitrage_bot.get_current_balance(),
            'open_positions': len(arbitrage_bot.trade_executor.open_positions),
            'daily_profit': await arbitrage_bot.get_daily_profit(),
            'win_rate': await arbitrage_bot.get_win_rate(),
            'average_trade_duration': await arbitrage_bot.get_average_trade_duration(),
            'sharpe_ratio': await arbitrage_bot.get_sharpe_ratio(),
        }
        logger.info(f"Updated performance metrics: {self.performance_metrics}")

    async def check_alerts(self):
        for alert in self.alerts:
            if alert['condition'](self.performance_metrics):
                await alert['callback'](self.performance_metrics)

    def add_alert(self, name: str, condition, callback):
        self.alerts.append({
            'name': name,
            'condition': condition,
            'callback': callback
        })

    def get_current_metrics(self) -> Dict:
        return self.performance_metrics

    async def generate_performance_report(self) -> str:
        report = "Real-Time Performance Report\n\n"
        for metric, value in self.performance_metrics.items():
            report += f"{metric.replace('_', ' ').title()}: {value}\n"
        return report