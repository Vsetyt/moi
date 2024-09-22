import tweepy
import praw
import asyncio
from typing import List, Dict
import aiohttp
import json

class SocialMediaIntegration:
    def __init__(self, config: Dict):
        self.twitter_api = self._setup_twitter(config['twitter'])
        self.reddit_api = self._setup_reddit(config['reddit'])
        self.telegram_token = config['telegram']['bot_token']
        self.telegram_channel_id = config['telegram']['channel_id']

    def _setup_twitter(self, config: Dict) -> tweepy.API:
        auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
        auth.set_access_token(config['access_token'], config['access_token_secret'])
        return tweepy.API(auth)

    def _setup_reddit(self, config: Dict) -> praw.Reddit:
        return praw.Reddit(
            client_id=config['client_id'],
            client_secret=config['client_secret'],
            user_agent=config['user_agent']
        )

    async def post_to_twitter(self, message: str):
        try:
            self.twitter_api.update_status(message)
            print(f"Posted to Twitter: {message}")
        except tweepy.TweepError as e:
            print(f"Error posting to Twitter: {e}")

    async def post_to_reddit(self, subreddit: str, title: str, content: str):
        try:
            self.reddit_api.subreddit(subreddit).submit(title, selftext=content)
            print(f"Posted to Reddit (r/{subreddit}): {title}")
        except praw.exceptions.PRAWException as e:
            print(f"Error posting to Reddit: {e}")

    async def post_to_telegram(self, message: str):
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            "chat_id": self.telegram_channel_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as response:
                if response.status == 200:
                    print(f"Posted to Telegram: {message}")
                else:
                    print(f"Error posting to Telegram: {await response.text()}")

    async def get_twitter_sentiment(self, hashtag: str, count: int = 100) -> float:
        tweets = self.twitter_api.search(q=hashtag, count=count)
        # This is a placeholder for sentiment analysis. In a real-world scenario,
        # you'd use a more sophisticated sentiment analysis method.
        sentiment_sum = sum(1 if 'positive' in tweet.text.lower() else -1 for tweet in tweets)
        return sentiment_sum / count

    async def get_reddit_sentiment(self, subreddit: str, limit: int = 100) -> float:
        submissions = self.reddit_api.subreddit(subreddit).hot(limit=limit)
        # Again, this is a placeholder for sentiment analysis
        sentiment_sum = sum(1 if submission.score > 0 else -1 for submission in submissions)
        return sentiment_sum / limit

    async def monitor_social_media(self, keywords: List[str]):
        while True:
            for keyword in keywords:
                twitter_sentiment = await self.get_twitter_sentiment(keyword)
                reddit_sentiment = await self.get_reddit_sentiment('cryptocurrency')
                
                message = (f"Social Media Sentiment for '{keyword}':\n"
                           f"Twitter: {twitter_sentiment:.2f}\n"
                           f"Reddit: {reddit_sentiment:.2f}")
                
                await self.post_to_telegram(message)
            
            await asyncio.sleep(3600)  # Wait for an hour before the next update

    async def announce_trade(self, trade_info: Dict):
        message = (f"New Trade Executed:\n"
                   f"Symbol: {trade_info['symbol']}\n"
                   f"Side: {trade_info['side']}\n"
                   f"Price: {trade_info['price']}\n"
                   f"Quantity: {trade_info['quantity']}\n"
                   f"Profit: {trade_info['profit']:.2f} USDT")
        
        await asyncio.gather(
            self.post_to_twitter(message),
            self.post_to_reddit('algotrading', 'New Trade Executed', message),
            self.post_to_telegram(message)
        )

    async def daily_report(self, report: Dict):
        message = (f"Daily Trading Report:\n"
                   f"Total Trades: {report['total_trades']}\n"
                   f"Profitable Trades: {report['profitable_trades']}\n"
                   f"Total Profit: {report['total_profit']:.2f} USDT\n"
                   f"Win Rate: {report['win_rate']:.2%}\n"
                   f"Best Trade: {report['best_trade']:.2f} USDT\n"
                   f"Worst Trade: {report['worst_trade']:.2f} USDT")
        
        await asyncio.gather(
            self.post_to_twitter(message),
            self.post_to_reddit('algotrading', 'Daily Trading Report', message),
            self.post_to_telegram(message)
        )