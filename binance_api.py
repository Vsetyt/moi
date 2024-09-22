import asyncio
import hmac
import hashlib
import time
from typing import Dict, List
import aiohttp
from urllib.parse import urlencode

class BinanceAPI:
    def __init__(self, api_key: str, api_secret: str):
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.BASE_URL = 'https://api.binance.com'

    async def _request(self, method: str, endpoint: str, params: Dict = None) -> Dict:
        url = f"{self.BASE_URL}{endpoint}"
        headers = {'X-MBX-APIKEY': self.API_KEY}
        
        if params:
            query_string = urlencode(params)
            signature = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
            params['signature'] = signature

        async with aiohttp.ClientSession() as session:
            if method == 'GET':
                async with session.get(url, headers=headers, params=params) as response:
                    return await response.json()
            elif method == 'POST':
                async with session.post(url, headers=headers, data=params) as response:
                    return await response.json()

    async def get_exchange_info(self) -> Dict:
        return await self._request('GET', '/api/v3/exchangeInfo')

    async def get_account_balance(self) -> List[Dict]:
        params = {'timestamp': int(time.time() * 1000)}
        account_info = await self._request('GET', '/api/v3/account', params)
        return account_info['balances']

    async def get_orderbook(self, symbol: str, limit: int = 100) -> Dict:
        params = {'symbol': symbol, 'limit': limit}
        return await self._request('GET', '/api/v3/depth', params)

    async def place_order(self, symbol: str, side: str, type: str, quantity: float, price: float = None) -> Dict:
        params = {
            'symbol': symbol,
            'side': side,
            'type': type,
            'quantity': quantity,
            'timestamp': int(time.time() * 1000)
        }
        if price:
            params['price'] = price
        return await self._request('POST', '/api/v3/order', params)

    async def get_open_orders(self, symbol: str = None) -> List[Dict]:
        params = {'timestamp': int(time.time() * 1000)}
        if symbol:
            params['symbol'] = symbol
        return await self._request('GET', '/api/v3/openOrders', params)

    async def cancel_order(self, symbol: str, order_id: int) -> Dict:
        params = {
            'symbol': symbol,
            'orderId': order_id,
            'timestamp': int(time.time() * 1000)
        }
        return await self._request('DELETE', '/api/v3/order', params)

    async def get_klines(self, symbol: str, interval: str, limit: int = 500) -> List[List]:
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return await self._request('GET', '/api/v3/klines', params)

    async def get_24hr_ticker(self, symbol: str) -> Dict:
        params = {'symbol': symbol}
        return await self._request('GET', '/api/v3/ticker/24hr', params)

    async def get_symbol_price_ticker(self, symbol: str) -> Dict:
        params = {'symbol': symbol}
        return await self._request('GET', '/api/v3/ticker/price', params)

    async def get_markets(self) -> List[Dict]:
        exchange_info = await self.get_exchange_info()
        return [{'symbol': s['symbol'], 'base_asset': s['baseAsset'], 'quote_asset': s['quoteAsset']}
                for s in exchange_info['symbols'] if s['status'] == 'TRADING']