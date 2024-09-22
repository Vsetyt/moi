import asyncio
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class AutoTrader:
    def __init__(self, arbitrage_bot, config: Dict):
        self.arbitrage_bot = arbitrage_bot
        self.config = config
        self.is_running = False
        self.trade_lock = asyncio.Lock()

    async def start(self):
        self.is_running = True
        while self.is_running:
            await self.execute_trading_cycle()
            await asyncio.sleep(self.config['trading_interval'])

    async def stop(self):
        self.is_running = False

    async def execute_trading_cycle(self):
        async with self.trade_lock:
            try:
                opportunities = await self.arbitrage_bot.find_arbitrage_opportunities()
                for opportunity in opportunities:
                    if self.should_execute_trade(opportunity):
                        await self.execute_trade(opportunity)
            except Exception as e:
                logger.error(f"Error in trading cycle: {str(e)}")

    def should_execute_trade(self, opportunity: Dict) -> bool:
        return (
            opportunity['profit_percent'] >= self.config['min_profit_percent'] and
            opportunity['volume'] <= self.config['max_trade_volume'] and
            self.arbitrage_bot.risk_manager.should_open_position(opportunity['volume'])
        )

    async def execute_trade(self, opportunity: Dict):
        try:
            result = await self.arbitrage_bot.execute_arbitrage(opportunity)
            if result['status'] == 'success':
                logger.info(f"Auto trade executed successfully: {result}")
                await self.arbitrage_bot.notification_manager.send_trade_notification(result)
            else:
                logger.warning(f"Auto trade failed: {result}")
        except Exception as e:
            logger.error(f"Error executing auto trade: {str(e)}")

    async def update_config(self, new_config: Dict):
        self.config.update(new_config)
        logger.info(f"Auto trader config updated: {self.config}")