import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ArbitrageLogic:
    def __init__(self, session_data, binance_api):
        self.session_data = session_data
        self.binance_api = binance_api
        self.opportunities = {}
        self.last_update = {}

    async def find_triangular_arbitrage_opportunities(self, prices, volumes, graph):
        opportunities = []
        for start_symbol in graph:
            for mid_symbol in graph[start_symbol]:
                for end_symbol in graph[mid_symbol]:
                    if end_symbol == start_symbol:
                        try:
                            path = [start_symbol, mid_symbol, end_symbol]
                            if not all(self.get_price(prices, s1, s2) for s1, s2 in zip(path, path[1:])):
                                continue
                            profit = self.calculate_profit(path, prices)
                            if profit > self.session_data.min_profit_percent:
                                volume = min(self.get_volume(volumes, s1, s2) for s1, s2 in zip(path, path[1:]))
                                if volume >= self.session_data.min_volume:
                                    volatility = self.calculate_volatility(path, prices)
                                    if self.session_data.min_volatility_percent <= volatility <= self.session_data.max_volatility_percent:
                                        opportunity = {
                                            'path': '->'.join(path),
                                            'profit': profit,
                                            'volume': volume,
                                            'volatility': volatility,
                                            'timestamp': datetime.now()
                                        }
                                        opportunities.append(opportunity)
                                        self.update_opportunity(opportunity)
                        except Exception as e:
                            logger.error(f"Ошибка при анализе пути {start_symbol}->{mid_symbol}->{end_symbol}: {str(e)}")
        return opportunities

    def get_price(self, prices, symbol1, symbol2):
        pair = f"{symbol1}{symbol2}"
        if pair in prices and 'price' in prices[pair]:
            return prices[pair]['price']
        pair = f"{symbol2}{symbol1}"
        if pair in prices and 'price' in prices[pair]:
            return 1 / prices[pair]['price']
        return None

    def get_volume(self, volumes, symbol1, symbol2):
        pair = f"{symbol1}{symbol2}"
        if pair in volumes:
            return volumes[pair]
        pair = f"{symbol2}{symbol1}"
        if pair in volumes:
            return volumes[pair]
        return 0

    def calculate_profit(self, path, prices):
        rate = 1
        for i in range(len(path) - 1):
            price = self.get_price(prices, path[i], path[i+1])
            if price is None:
                return 0
            rate *= price
        return (rate - 1) * 100

    def calculate_volatility(self, path, prices):
        volatilities = []
        for i in range(len(path) - 1):
            pair = f"{path[i]}{path[i+1]}"
            if pair in prices and 'volatility' in prices[pair]:
                volatilities.append(prices[pair]['volatility'])
            else:
                pair = f"{path[i+1]}{path[i]}"
                if pair in prices and 'volatility' in prices[pair]:
                    volatilities.append(prices[pair]['volatility'])
        return max(volatilities) if volatilities else 0

    def update_opportunity(self, opportunity):
        exchange = self.binance_api.exchange_name
        if exchange not in self.opportunities:
            self.opportunities[exchange] = []
        self.opportunities[exchange] = [op for op in self.opportunities[exchange] if (datetime.now() - op['timestamp']).total_seconds() < 300]
        self.opportunities[exchange].append(opportunity)
        self.opportunities[exchange].sort(key=lambda x: x['profit'], reverse=True)
        self.opportunities[exchange] = self.opportunities[exchange][:10]
        self.last_update[exchange] = datetime.now()

    async def get_last_opportunity(self, exchange):
        if exchange not in self.last_update or (datetime.now() - self.last_update[exchange]).total_seconds() > 60:
            await self.update_opportunities(exchange)
        if exchange in self.opportunities and self.opportunities[exchange]:
            return self.opportunities[exchange][0]
        return None

    async def update_opportunities(self, exchange):
        try:
            prices = await self.binance_api.get_prices()
            volumes = await self.binance_api.get_24h_volumes()
            graph = await self.binance_api.build_market_graph()
            await self.find_triangular_arbitrage_opportunities(prices, volumes, graph)
        except Exception as e:
            logger.error(f"Ошибка при обновлении возможностей для биржи {exchange}: {str(e)}")

    async def send_notification(self, context, opportunity, user_id):
        text = f"Найдена арбитражная возможность:\n" \
               f"Путь: {opportunity['path']}\n" \
               f"Прибыль: {opportunity['profit']:.2f}%\n" \
               f"Объем: {opportunity['volume']:.2f} USDT\n" \
               f"Волатильность: {opportunity['volatility']:.2f}%\n" \
               f"Время: {opportunity['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}"
        keyboard = [[InlineKeyboardButton("Выполнить арбитраж", callback_data=f"execute_arbitrage_{opportunity['path']}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        return await context.bot.send_message(chat_id=user_id, text=text, reply_markup=reply_markup)