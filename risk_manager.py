import logging
from typing import Dict

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, initial_balance: float, max_risk_per_trade: float = 0.02):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.max_risk_per_trade = max_risk_per_trade
        self.open_positions: Dict[str, float] = {}

    def calculate_position_size(self, opportunity: Dict) -> float:
        max_loss = self.current_balance * self.max_risk_per_trade
        stop_loss_percent = opportunity.get('stop_loss', 0.01)  # 1% по умолчанию
        position_size = max_loss / stop_loss_percent
        return min(position_size, opportunity['volume'])

    def can_open_position(self, opportunity: Dict) -> bool:
        total_risk = sum(self.open_positions.values())
        new_position_risk = self.calculate_position_size(opportunity) * opportunity.get('stop_loss', 0.01)
        return (total_risk + new_position_risk) <= (self.current_balance * self.max_risk_per_trade * 3)

    def add_position(self, trade_id: str, position_size: float, stop_loss: float):
        self.open_positions[trade_id] = position_size * stop_loss

    def remove_position(self, trade_id: str):
        if trade_id in self.open_positions:
            del self.open_positions[trade_id]

    def update_balance(self, new_balance: float):
        self.current_balance = new_balance
        logger.info(f"Balance updated to {new_balance}")

    def get_risk_level(self) -> str:
        total_risk = sum(self.open_positions.values())
        risk_percentage = (total_risk / self.current_balance) * 100
        if risk_percentage < 1:
            return "Низкий"
        elif risk_percentage < 2:
            return "Средний"
        else:
            return "Высокий"