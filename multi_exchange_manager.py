from typing import Dict
from binance_api import BinanceAPI
# Импортируйте другие API бирж по мере необходимости

class MultiExchangeManager:
    def __init__(self):
        self.exchanges: Dict[str, object] = {}

    def add_exchange(self, name: str, api_key: str, api_secret: str):
        if name.lower() == 'binance':
            self.exchanges[name] = BinanceAPI(api_key, api_secret)
        # Добавьте другие биржи по мере необходимости
        # elif name.lower() == 'kraken':
        #     self.exchanges[name] = KrakenAPI(api_key, api_secret)

    async def get_prices(self, exchange_name: str):
        if exchange_name in self.exchanges:
            return await self.exchanges[exchange_name].get_prices()
        raise ValueError(f"Exchange {exchange_name} not found")

    async def execute_trade(self, exchange_name: str, trade_data: Dict):
        if exchange_name in self.exchanges:
            return await self.exchanges[exchange_name].execute_arbitrage_trade(trade_data)
        raise ValueError(f"Exchange {exchange_name} not found")

    async def get_balance(self, exchange_name: str, asset: str):
        if exchange_name in self.exchanges:
            return await self.exchanges[exchange_name].get_balance(asset)
        raise ValueError(f"Exchange {exchange_name} not found")

    # Добавьте другие методы для работы с биржами по мере необходимости