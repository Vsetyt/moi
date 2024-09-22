import aiohttp
import asyncio
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class ExternalDataProvider:
    def __init__(self):
        self.session = None

    async def start(self):
        self.session = aiohttp.ClientSession()

    async def stop(self):
        if self.session:
            await self.session.close()

    async def get_market_news(self) -> List[Dict]:
        try:
            async with self.session.get('https://api.example.com/market_news') as response:
                if response.status == 200:
                    data = await response.json()
                    return data['news']
                else:
                    logger.error(f"Failed to fetch market news. Status: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching market news: {str(e)}")
            return []

    async def get_economic_calendar(self) -> List[Dict]:
        try:
            async with self.session.get('https://api.example.com/economic_calendar') as response:
                if response.status == 200:
                    data = await response.json()
                    return data['events']
                else:
                    logger.error(f"Failed to fetch economic calendar. Status: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching economic calendar: {str(e)}")
            return []

    async def get_market_sentiment(self) -> Dict:
        try:
            async with self.session.get('https://api.example.com/market_sentiment') as response:
                if response.status == 200:
                    data = await response.json()
                    return data['sentiment']
                else:
                    logger.error(f"Failed to fetch market sentiment. Status: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"Error fetching market sentiment: {str(e)}")
            return {}