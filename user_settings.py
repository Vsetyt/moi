from typing import Dict
import json

class UserSettings:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.settings: Dict = {
            'notifications': {
                'trade_execution': True,
                'trade_closure': True,
                'daily_report': True
            },
            'risk_level': 'medium',
            'preferred_exchanges': ['binance', 'kraken'],
            'max_concurrent_trades': 3,
            'auto_optimization': False
        }

    def update_setting(self, key: str, value):
        keys = key.split('.')
        target = self.settings
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value

    def get_setting(self, key: str):
        keys = key.split('.')
        target = self.settings
        for k in keys:
            target = target.get(k, {})
        return target

    def save(self):
        with open(f'user_settings_{self.user_id}.json', 'w') as f:
            json.dump(self.settings, f)

    def load(self):
        try:
            with open(f'user_settings_{self.user_id}.json', 'r') as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            pass  # Используем настройки по умолчанию