import json
import os

class SessionData:
    def __init__(self):
        self.initial_amount = 100  # Начальная сумма в USDT
        self.min_profit_percent = 0.5  # Минимальный процент прибыли
        self.max_volatility_percent = 1.0  # Максимальная допустимая волатильность
        self.min_volatility_percent = 0.1  # Минимальная требуемая волатильность
        self.min_volume = 10000  # Минимальный объем торгов в USDT
        self.fixed_amount = 0  # Фиксированная сумма для автоматической торговли
        self.fixed_percent = 0  # Фиксированный процент для автоматической торговли
        self.file_path = 'session_data_{}.json'

    def save(self, user_id):
        data = {
            'initial_amount': self.initial_amount,
            'min_profit_percent': self.min_profit_percent,
            'max_volatility_percent': self.max_volatility_percent,
            'min_volatility_percent': self.min_volatility_percent,
            'min_volume': self.min_volume,
            'fixed_amount': self.fixed_amount,
            'fixed_percent': self.fixed_percent
        }
        with open(self.file_path.format(user_id), 'w') as f:
            json.dump(data, f)

    def load(self, user_id):
        file_path = self.file_path.format(user_id)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.initial_amount = data.get('initial_amount', self.initial_amount)
            self.min_profit_percent = data.get('min_profit_percent', self.min_profit_percent)
            self.max_volatility_percent = data.get('max_volatility_percent', self.max_volatility_percent)
            self.min_volatility_percent = data.get('min_volatility_percent', self.min_volatility_percent)
            self.min_volume = data.get('min_volume', self.min_volume)
            self.fixed_amount = data.get('fixed_amount', self.fixed_amount)
            self.fixed_percent = data.get('fixed_percent', self.fixed_percent)

    def reset(self, user_id):
        file_path = self.file_path.format(user_id)
        if os.path.exists(file_path):
            os.remove(file_path)
        self.__init__()

    def update(self, user_id, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save(user_id)

    def get_settings(self):
        return {
            'Начальная сумма': f'{self.initial_amount} USDT',
            'Минимальный процент прибыли': f'{self.min_profit_percent}%',
            'Максимальная волатильность': f'{self.max_volatility_percent}%',
            'Минимальная волатильность': f'{self.min_volatility_percent}%',
            'Минимальный объем торгов': f'{self.min_volume} USDT',
            'Фиксированная сумма': f'{self.fixed_amount} USDT',
            'Фиксированный процент': f'{self.fixed_percent}%'
        }