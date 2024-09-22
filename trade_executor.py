import logging
from typing import Dict, List
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    CONSERVATIVE = 1
    MODERATE = 2
    AGGRESSIVE = 3

class TradeExecutor:
    def __init__(self, binance_api, risk_manager, db_manager, notification_manager):
        self.binance_api = binance_api
        self.risk_manager = risk_manager
        self.db_manager = db_manager
        self.notification_manager = notification_manager
        self.exchanges = {}
        self.is_trading_enabled = False
        self.max_position_size = 100  # в USDT
        self.max_concurrent_trades = 3
        self.stop_loss_percent = 1.0
        self.take_profit_percent = 2.0
        self.trading_mode = TradingMode.MODERATE
        self.open_positions: Dict[str, Dict] = {}
        self.test_mode = True

    def add_exchange(self, exchange_name: str, exchange_api):
        self.exchanges[exchange_name] = exchange_api
        logger.info(f"Добавлена биржа: {exchange_name}")

    def enable_trading(self, enabled: bool):
        self.is_trading_enabled = enabled
        status = 'включена' if enabled else 'выключена'
        logger.info(f"Автоматическая торговля {status}")
        return f"Автоматическая торговля {status}"

    def set_max_position_size(self, size: float):
        self.max_position_size = size
        logger.info(f"Максимальный размер позиции установлен на {size} USDT")
        return f"Максимальный размер позиции установлен на {size} USDT"

    def set_max_concurrent_trades(self, count: int):
        self.max_concurrent_trades = count
        logger.info(f"Максимальное количество одновременных сделок установлено на {count}")
        return f"Максимальное количество одновременных сделок установлено на {count}"

    def set_stop_loss(self, percent: float):
        self.stop_loss_percent = percent
        logger.info(f"Stop-loss установлен на {percent}%")
        return f"Stop-loss установлен на {percent}%"

    def set_take_profit(self, percent: float):
        self.take_profit_percent = percent
        logger.info(f"Take-profit установлен на {percent}%")
        return f"Take-profit установлен на {percent}%"

    def set_trading_mode(self, mode: TradingMode):
        self.trading_mode = mode
        logger.info(f"Режим торговли установлен на {mode.name}")
        return f"Режим торговли установлен на {mode.name}"

    def set_test_mode(self, enabled: bool):
        self.test_mode = enabled
        status = 'включен' if enabled else 'выключен'
        logger.info(f"Тестовый режим {status}")
        return f"Тестовый режим {status}"

    async def execute_arbitrage(self, exchange: str, opportunity: Dict, position_size: float):
        if not self.is_trading_enabled:
            return "Торговля отключена"
        if exchange not in self.exchanges:
            return f"Биржа {exchange} не найдена"
        exchange_positions = [p for p in self.open_positions.values() if p['exchange'] == exchange]
        if len(exchange_positions) >= self.max_concurrent_trades:
            return f"Достигнуто максимальное количество одновременных сделок на бирже {exchange}"
        trade_size = min(position_size, self.max_position_size, opportunity['volume'])
        if self.test_mode:
            logger.info(f"Тестовый режим: Выполнение арбитража на {exchange} {opportunity['path']} с размером {trade_size} USDT")
            return f"Тестовый режим: Арбитраж выполнен на {exchange}"
        try:
            trade_id = await self.exchanges[exchange].execute_arbitrage_trade(opportunity['path'], trade_size)
            self.open_positions[trade_id] = {
                'exchange': exchange,
                'path': opportunity['path'],
                'size': trade_size,
                'entry_prices': opportunity['prices'],
            }
            logger.info(f"Открыта арбитражная позиция {trade_id} на {exchange} по пути {opportunity['path']}")
            return f"Открыта арбитражная позиция {trade_id} на {exchange}"
        except Exception as e:
            logger.error(f"Ошибка при выполнении арбитража на {exchange}: {str(e)}")
            return f"Ошибка при выполнении арбитража на {exchange}: {str(e)}"

    async def monitor_positions(self):
        for trade_id, position in list(self.open_positions.items()):
            try:
                exchange = self.exchanges[position['exchange']]
                current_prices = await exchange.get_current_prices(position['path'])
                profit_loss = self.calculate_profit_loss(position, current_prices)
                if profit_loss >= self.take_profit_percent:
                    await self.close_position(trade_id, 'take_profit')
                elif profit_loss <= -self.stop_loss_percent:
                    await self.close_position(trade_id, 'stop_loss')
            except Exception as e:
                logger.error(f"Ошибка при мониторинге позиции {trade_id}: {str(e)}")

    async def close_position(self, trade_id: str, reason: str):
        if trade_id not in self.open_positions:
            return f"Позиция {trade_id} не найдена"
        position = self.open_positions[trade_id]
        exchange = position['exchange']
        if self.test_mode:
            logger.info(f"Тестовый режим: Закрытие позиции {trade_id} на {exchange} по причине {reason}")
            del self.open_positions[trade_id]
            return f"Тестовый режим: Позиция {trade_id} на {exchange} закрыта"
        try:
            result = await self.exchanges[exchange].close_arbitrage_trade(trade_id)
            logger.info(f"Закрыта позиция {trade_id} на {exchange} по причине {reason}")
            del self.open_positions[trade_id]
            self.risk_manager.remove_position(trade_id)
            # Обновляем информацию о сделке в базе данных
            self.db_manager.close_trade(trade_id, result['actual_profit'])
            # Отправляем уведомление пользователю
            await self.notification_manager.send_trade_closure(position['user_id'], {
                'id': trade_id,
                'path': position['path'],
                'actual_profit': result['actual_profit']
            })
            return f"Позиция {trade_id} на {exchange} закрыта по причине {reason}"
        except Exception as e:
            logger.error(f"Ошибка при закрытии позиции {trade_id} на {exchange}: {str(e)}")
            return f"Ошибка при закрытии позиции {trade_id} на {exchange}: {str(e)}"

    def calculate_profit_loss(self, position: Dict, current_prices: Dict) -> float:
        entry_prices = position['entry_prices']
        path = position['path']
        initial_amount = position['size']
        final_amount = initial_amount
        for i, symbol in enumerate(path):
            if i == 0:
                continue
            price_key = f"{path[i-1]}{path[i]}"
            if price_key in current_prices:
                final_amount *= current_prices[price_key] / entry_prices[price_key]
            else:
                price_key = f"{path[i]}{path[i-1]}"
                if price_key in current_prices:
                    final_amount /= current_prices[price_key] / entry_prices[price_key]
                else:
                    logger.error(f"Не удалось найти цену для пары {path[i-1]}-{path[i]}")
                    return 0
        profit_loss = (final_amount - initial_amount) / initial_amount * 100
        return profit_loss

    def get_open_positions(self) -> List[Dict]:
        return [{'id': k, **v} for k, v in self.open_positions.items()]

    def reset(self):
        self.open_positions.clear()
        logger.info("Сброс всех открытых позиций")
        return "Все открытые позиции сброшены"

    @staticmethod
    def get_trading_warning():
        return ("ВНИМАНИЕ: Автоматическая торговля сопряжена с высокими рисками. "
                "Используйте эту функцию на свой страх и риск. Убедитесь, что вы "
                "понимаете все риски, связанные с криптовалютной торговлей.")

    def apply_trading_mode(self):
        if self.trading_mode == TradingMode.CONSERVATIVE:
            self.max_position_size *= 0.5
            self.stop_loss_percent = 0.5
            self.take_profit_percent = 1.5
        elif self.trading_mode == TradingMode.AGGRESSIVE:
            self.max_position_size *= 2
            self.stop_loss_percent = 2.0
            self.take_profit_percent = 3.0
        # Для MODERATE режима оставляем настройки по умолчанию

async def trading_monitor(trade_executor):
    while True:
        await trade_executor.monitor_positions()
        await asyncio.sleep(10)  # Проверка каждые 10 секунд