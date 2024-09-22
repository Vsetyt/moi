import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        self.API_KEY = os.getenv('BINANCE_API_KEY')
        self.API_SECRET = os.getenv('BINANCE_API_SECRET')
        self.TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def load_config():
    return Config()