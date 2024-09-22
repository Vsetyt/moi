import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, initial_balance: float, max_risk_per_trade: float = 0.01):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.max_risk_per_trade = max_risk_per_trade
        self.open_positions: Dict[str, float] = {}

    def calculate_position_size(self, entry_price: float, stop_loss: float) -> float:
        risk_amount = self.current_balance * self.max_risk_per_trade
        position_size = risk_amount / (entry_price - stop_loss)
        return position_size

    def update_balance(self, new_balance: float):
        self.current_balance = new_balance

    def add_position(self, symbol: str, position_size: float):
        self.open_positions[symbol] = position_size

    def remove_position(self, symbol: str):
        if symbol in self.open_positions:
            del self.open_positions[symbol]

    def calculate_portfolio_risk(self) -> float:
        total_risk = sum(self.open_positions.values()) / self.current_balance
        return total_risk

    def should_open_position(self, new_position_size: float) -> bool:
        new_total_risk = self.calculate_portfolio_risk() + (new_position_size / self.current_balance)
        return new_total_risk <= 0.05  # Максимальный риск портфеля 5%

    def calculate_kelly_criterion(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        q = 1 - win_rate
        return (win_rate / q) - (avg_loss / avg_win)

    def adjust_position_size(self, kelly_percentage: float, position_size: float) -> float:
        return position_size * kelly_percentage