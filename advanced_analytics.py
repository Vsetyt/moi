import pandas as pd
import numpy as np
from typing import Dict, List
import matplotlib.pyplot as plt
import seaborn as sns
import io
import logging

logger = logging.getLogger(__name__)

class AdvancedAnalytics:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def generate_advanced_report(self, user_id: int, start_date: str, end_date: str) -> Dict:
        trades = self.db_manager.get_user_trades(user_id, start_date, end_date)
        df = pd.DataFrame(trades)
        
        if df.empty:
            return {"message": "No trade data available for the specified period"}

        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

        report = {
            "summary": self.generate_summary(df),
            "performance_metrics": self.calculate_performance_metrics(df),
            "trade_analysis": self.analyze_trades(df),
            "risk_metrics": self.calculate_risk_metrics(df),
            "visualizations": self.generate_visualizations(df)
        }

        return report

    def generate_summary(self, df: pd.DataFrame) -> Dict:
        return {
            "total_trades": len(df),
            "total_profit": df['profit'].sum(),
            "average_profit": df['profit'].mean(),
            "win_rate": (df['profit'] > 0).mean(),
            "best_trade": df['profit'].max(),
            "worst_trade": df['profit'].min(),
            "average_trade_duration": (df.index - df.index.shift()).mean().total_seconds() / 60  # в минутах
        }

    def calculate_performance_metrics(self, df: pd.DataFrame) -> Dict:
        daily_returns = df.resample('D')['profit'].sum()
        return {
            "sharpe_ratio": self.calculate_sharpe_ratio(daily_returns),
            "sortino_ratio": self.calculate_sortino_ratio(daily_returns),
            "profit_factor": df[df['profit'] > 0]['profit'].sum() / abs(df[df['profit'] < 0]['profit'].sum()),
            "expectancy": df['profit'].mean() / abs(df[df['profit'] < 0]['profit'].mean()),
            "average_win": df[df['profit'] > 0]['profit'].mean(),
            "average_loss": abs(df[df['profit'] < 0]['profit'].mean()),
            "win_loss_ratio": df[df['profit'] > 0]['profit'].mean() / abs(df[df['profit'] < 0]['profit'].mean())
        }

    def analyze_trades(self, df: pd.DataFrame) -> Dict:
        return {
            "most_profitable_pair": df.groupby('symbol')['profit'].sum().idxmax(),
            "least_profitable_pair": df.groupby('symbol')['profit'].sum().idxmin(),
            "best_day": df.resample('D')['profit'].sum().idxmax().strftime('%Y-%m-%d'),
            "worst_day": df.resample('D')['profit'].sum().idxmin().strftime('%Y-%m-%d'),
            "best_hour": df.groupby(df.index.hour)['profit'].mean().idxmax(),
            "worst_hour": df.groupby(df.index.hour)['profit'].mean().idxmin(),
            "consecutive_wins": self.calculate_consecutive_trades(df, 'win'),
            "consecutive_losses": self.calculate_consecutive_trades(df, 'loss')
        }

    def calculate_risk_metrics(self, df: pd.DataFrame) -> Dict:
        daily_returns = df.resample('D')['profit'].sum()
        cumulative_returns = (1 + daily_returns).cumprod()
        peak = cumulative_returns.expanding(min_periods=1).max()
        drawdown = (cumulative_returns / peak) - 1
        
        return {
            "max_drawdown": drawdown.min(),
            "average_drawdown": drawdown.mean(),
            "value_at_risk": daily_returns.quantile(0.05),  # 5% VaR
            "conditional_value_at_risk": daily_returns[daily_returns <= daily_returns.quantile(0.05)].mean(),
            "ulcer_index": np.sqrt(np.sum(drawdown**2) / len(drawdown)),
            "risk_of_ruin": self.calculate_risk_of_ruin(df)
        }

    def generate_visualizations(self, df: pd.DataFrame) -> Dict:
        return {
            "equity_curve": self.plot_equity_curve(df),
            "drawdown_chart": self.plot_drawdown_chart(df),
            "profit_distribution": self.plot_profit_distribution(df),
            "monthly_returns_heatmap": self.plot_monthly_returns_heatmap(df)
        }

    def calculate_sharpe_ratio(self, returns: pd.Series) -> float:
        return (returns.mean() / returns.std()) * np.sqrt(252)  # Годовой коэффициент Шарпа

    def calculate_sortino_ratio(self, returns: pd.Series) -> float:
        negative_returns = returns[returns < 0]
        downside_deviation = np.sqrt(np.sum(negative_returns**2) / len(returns))
        return (returns.mean() / downside_deviation) * np.sqrt(252)

    def calculate_consecutive_trades(self, df: pd.DataFrame, trade_type: str) -> int:
        streak = (df['profit'] > 0) if trade_type == 'win' else (df['profit'] < 0)
        return streak.groupby((streak != streak.shift()).cumsum()).sum().max()

    def calculate_risk_of_ruin(self, df: pd.DataFrame) -> float:
        p = (df['profit'] > 0).mean()  # вероятность выигрыша
        q = 1 - p  # вероятность проигрыша
        R = df[df['profit'] > 0]['profit'].mean() / abs(df[df['profit'] < 0]['profit'].mean())  # отношение средней прибыли к среднему убытку
        return (q / p) ** (1 / R) if p > q else 1

    def plot_equity_curve(self, df: pd.DataFrame) -> io.BytesIO:
        plt.figure(figsize=(12, 6))
        cumulative_profit = df['profit'].cumsum()
        plt.plot(df.index, cumulative_profit)
        plt.title('Equity Curve')
        plt.xlabel('Date')
        plt.ylabel('Cumulative Profit')
        plt.grid(True)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf

    def plot_drawdown_chart(self, df: pd.DataFrame) -> io.BytesIO:
        plt.figure(figsize=(12, 6))
        cumulative_profit = df['profit'].cumsum()
        peak = cumulative_profit.expanding(min_periods=1).max()
        drawdown = (cumulative_profit / peak) - 1
        plt.plot(df.index, drawdown)
        plt.title('Drawdown Chart')
        plt.xlabel('Date')
        plt.ylabel('Drawdown')
        plt.grid(True)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf

    def plot_profit_distribution(self, df: pd.DataFrame) -> io.BytesIO:
        plt.figure(figsize=(12, 6))
        sns.histplot(df['profit'], kde=True)
        plt.title('Profit Distribution')
        plt.xlabel('Profit')
        plt.ylabel('Frequency')
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf

    def plot_monthly_returns_heatmap(self, df: pd.DataFrame) -> io.BytesIO:
        plt.figure(figsize=(12, 8))
        monthly_returns = df.resample('M')['profit'].sum().unstack(level=0)
        sns.heatmap(monthly_returns, annot=True, fmt=".2f", cmap="RdYlGn")
        plt.title('Monthly Returns Heatmap')
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        return buf