import pandas as pd
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def calculate_metrics(self, user_id: int, start_date: str, end_date: str) -> Dict:
        trades = self.db_manager.get_user_trades(user_id, start_date, end_date)
        df = pd.DataFrame(trades)
        
        if df.empty:
            return {"message": "Нет данных о сделках за указанный период"}

        df['timestamp'] = pd.to_datetime(df['created_at'])
        df = df.set_index('timestamp')
        df['cumulative_profit'] = df['profit'].cumsum()

        total_profit = df['profit'].sum()
        win_rate = (df['profit'] > 0).mean()
        profit_factor = df[df['profit'] > 0]['profit'].sum() / abs(df[df['profit'] < 0]['profit'].sum())
        sharpe_ratio = self.calculate_sharpe_ratio(df['profit'])
        max_drawdown = self.calculate_max_drawdown(df['cumulative_profit'])
        
        return {
            "total_profit": total_profit,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "total_trades": len(df),
            "average_profit": df['profit'].mean(),
            "profit_std": df['profit'].std()
        }

    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series) -> float:
        return np.sqrt(252) * returns.mean() / returns.std()

    @staticmethod
    def calculate_max_drawdown(equity_curve: pd.Series) -> float:
        return (equity_curve.cummax() - equity_curve).max() / equity_curve.cummax().max()

    def generate_performance_report(self, user_id: int, start_date: str, end_date: str) -> str:
        metrics = self.calculate_metrics(user_id, start_date, end_date)
        
        if "message" in metrics:
            return metrics["message"]

        report = (
            f"Отчет о производительности ({start_date} - {end_date}):\n\n"
            f"Общая прибыль: {metrics['total_profit']:.2f} USDT\n"
            f"Винрейт: {metrics['win_rate']:.2%}\n"
            f"Profit Factor: {metrics['profit_factor']:.2f}\n"
            f"Коэффициент Шарпа: {metrics['sharpe_ratio']:.2f}\n"
            f"Максимальная просадка: {metrics['max_drawdown']:.2%}\n"
            f"Всего сделок: {metrics['total_trades']}\n"
            f"Средняя прибыль: {metrics['average_profit']:.2f} USDT\n"
            f"Стандартное отклонение прибыли: {metrics['profit_std']:.2f} USDT"
        )
        return report