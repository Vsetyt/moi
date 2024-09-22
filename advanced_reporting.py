import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
import numpy as np
from scipy import stats
import plotly.graph_objects as go
import plotly.express as px
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from database_manager import DatabaseManager
import asyncio
import json

class AdvancedReporting:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def generate_advanced_report(self, user_id: int, start_date: str, end_date: str) -> Dict:
        trades = await self.db_manager.get_user_trades(user_id, start_date, end_date)
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
            "visualizations": self.generate_visualizations(df),
            "trade_timing": self.analyze_trade_timing(df),
            "trade_size_analysis": self.analyze_trade_size(df),
            "market_condition_analysis": self.analyze_market_conditions(df),
            "win_loss_streaks": self.calculate_win_loss_streaks(df),
            "strategy_correlations": self.analyze_trade_correlations(df),
            "advanced_risk_metrics": self.calculate_advanced_risk_metrics(df)
        }

        self.generate_pdf_report(report, f"report_{user_id}_{start_date}_{end_date}.pdf")

        return report

    def generate_summary(self, df: pd.DataFrame) -> Dict:
        return {
            "total_trades": len(df),
            "total_profit": df['profit'].sum(),
            "average_profit": df['profit'].mean(),
            "win_rate": (df['profit'] > 0).mean(),
            "best_trade": df['profit'].max(),
            "worst_trade": df['profit'].min(),
            "average_trade_duration": (df.index - df.index.shift()).mean().total_seconds() / 60  # in minutes
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
        return (returns.mean() / returns.std()) * np.sqrt(252)  # Annualized Sharpe ratio

    def calculate_sortino_ratio(self, returns: pd.Series) -> float:
        negative_returns = returns[returns < 0]
        downside_deviation = np.sqrt(np.sum(negative_returns**2) / len(returns))
        return (returns.mean() / downside_deviation) * np.sqrt(252)

    def calculate_consecutive_trades(self, df: pd.DataFrame, trade_type: str) -> int:
        streak = (df['profit'] > 0) if trade_type == 'win' else (df['profit'] < 0)
        return streak.groupby((streak != streak.shift()).cumsum()).sum().max()

    def calculate_risk_of_ruin(self, df: pd.DataFrame) -> float:
        p = (df['profit'] > 0).mean()  # probability of winning
        q = 1 - p  # probability of losing
        R = df[df['profit'] > 0]['profit'].mean() / abs(df[df['profit'] < 0]['profit'].mean())  # win/loss ratio
        return (q / p) ** (1 / R) if p > q else 1

    def plot_equity_curve(self, df: pd.DataFrame) -> str:
        cumulative_profit = df['profit'].cumsum()
        fig = go.Figure(data=go.Scatter(x=df.index, y=cumulative_profit, mode='lines'))
        fig.update_layout(title='Equity Curve', xaxis_title='Date', yaxis_title='Cumulative Profit')
        return fig.to_html(full_html=False)

    def plot_drawdown_chart(self, df: pd.DataFrame) -> str:
        cumulative_profit = df['profit'].cumsum()
        peak = cumulative_profit.expanding(min_periods=1).max()
        drawdown = (cumulative_profit / peak) - 1
        fig = go.Figure(data=go.Scatter(x=df.index, y=drawdown, mode='lines', fill='tozeroy'))
        fig.update_layout(title='Drawdown Chart', xaxis_title='Date', yaxis_title='Drawdown')
        return fig.to_html(full_html=False)

    def plot_profit_distribution(self, df: pd.DataFrame) -> str:
        fig = px.histogram(df, x='profit', nbins=50, title='Profit Distribution')
        return fig.to_html(full_html=False)

    def plot_monthly_returns_heatmap(self, df: pd.DataFrame) -> str:
        monthly_returns = df.resample('M')['profit'].sum().unstack(level=0)
        fig = px.imshow(monthly_returns, color_continuous_scale='RdYlGn', title='Monthly Returns Heatmap')
        return fig.to_html(full_html=False)

    def analyze_trade_timing(self, df: pd.DataFrame) -> Dict:
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        
        hourly_performance = df.groupby('hour')['profit'].mean()
        daily_performance = df.groupby('day_of_week')['profit'].mean()
        
        return {
            'best_trading_hour': hourly_performance.idxmax(),
            'worst_trading_hour': hourly_performance.idxmin(),
            'best_trading_day': daily_performance.idxmax(),
            'worst_trading_day': daily_performance.idxmin(),
            'hourly_performance': hourly_performance.to_dict(),
            'daily_performance': daily_performance.to_dict()
        }

    def analyze_trade_size(self, df: pd.DataFrame) -> Dict:
        df['trade_size'] = df['entry_price'] * df['quantity']
        size_groups = pd.qcut(df['trade_size'], q=5)
        size_performance = df.groupby(size_groups)['profit'].mean()
        
        return {
            'best_performing_size': size_performance.idxmax(),
            'worst_performing_size': size_performance.idxmin(),
            'size_performance': size_performance.to_dict()
        }

    def analyze_market_conditions(self, df: pd.DataFrame) -> Dict:
        df['market_trend'] = np.where(df['close'] > df['close'].shift(20), 'bullish', 'bearish')
        df['volatility'] = df['close'].pct_change().rolling(window=20).std()
        volatility_groups = pd.qcut(df['volatility'], q=3, labels=['low', 'medium', 'high'])
        
        trend_performance = df.groupby('market_trend')['profit'].mean()
        volatility_performance = df.groupby(volatility_groups)['profit'].mean()
        
        return {
            'bullish_performance': trend_performance['bullish'],
            'bearish_performance': trend_performance['bearish'],
            'low_volatility_performance': volatility_performance['low'],
            'medium_volatility_performance': volatility_performance['medium'],
            'high_volatility_performance': volatility_performance['high']
        }

    def calculate_win_loss_streaks(self, df: pd.DataFrame) -> Dict:
        df['win'] = df['profit'] > 0
        streaks = df['win'].groupby((df['win'] != df['win'].shift()).cumsum()).cumcount() + 1
        win_streaks = streaks[df['win']]
        loss_streaks = streaks[~df['win']]
        
        return {
            'max_win_streak': win_streaks.max(),
            'max_loss_streak': loss_streaks.max(),
            'average_win_streak': win_streaks.mean(),
            'average_loss_streak': loss_streaks.mean()
        }

    def analyze_trade_correlations(self, df: pd.DataFrame) -> Dict:
        strategy_returns = df.pivot(columns='strategy', values='profit')
        correlation_matrix = strategy_returns.corr()
        
        return {
            'correlation_matrix': correlation_matrix.to_dict(),
            'most_correlated_pair': correlation_matrix.unstack().sort_values(ascending=False).index[1],
            'least_correlated_pair': correlation_matrix.unstack().sort_values().index[0]
        }

    def calculate_advanced_risk_metrics(self, df: pd.DataFrame) -> Dict:
        returns = df['profit'].pct_change()
        
        return {
            'kurtosis': returns.kurtosis(),
            'skewness': returns.skew(),
            'tail_ratio': abs(returns.quantile(0.95)) / abs(returns.quantile(0.05)),
            'omega_ratio': self.calculate_omega_ratio(returns)
        }

    def calculate_omega_ratio(self, returns: pd.Series, threshold: float = 0) -> float:
        return (returns[returns > threshold].sum() / abs(returns[returns < threshold].sum()))

    def generate_pdf_report(self, report: Dict, filename: str):
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, "Advanced Trading Report")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, f"Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Summary
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 100, "Summary")
        c.setFont("Helvetica", 12)
        y = height - 120
        for key, value in report['summary'].items():
            c.drawString(50, y, f"{key.replace('_', ' ').title()}: {value:.2f}")
            y -= 20

        # Performance Metrics
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y - 20, "Performance Metrics")
        c.setFont("Helvetica", 12)
        y -= 40
        for key, value in report['performance_metrics'].items():
            c.drawString(50, y, f"{key.replace('_', ' ').title()}: {value:.2f}")
            y -= 20

        # Risk Metrics
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height - 50, "Risk Metrics")
        c.setFont("Helvetica", 12)
        y = height - 70
        for key, value in report['risk_metrics'].items():
            c.drawString(50, y, f"{key.replace('_', ' ').title()}: {value:.2f}")
            y -= 20

        # Trade Analysis
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y - 20, "Trade Analysis")
        c.setFont("Helvetica", 12)
        y -= 40
        for key, value in report['trade_analysis'].items():
            c.drawString(50, y, f"{key.replace('_', ' ').title()}: {value}")
            y -= 20

        # New sections
        sections = [
            ("Trade Timing Analysis", report['trade_timing']),
            ("Trade Size Analysis", report['trade_size_analysis']),
            ("Market Condition Analysis", report['market_condition_analysis']),
            ("Win/Loss Streaks", report['win_loss_streaks']),
            ("Strategy Correlations", report['strategy_correlations']),
            ("Advanced Risk Metrics", report['advanced_risk_metrics'])
        ]

        for title, data in sections:
            c.showPage()
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height - 50, title)
            c.setFont("Helvetica", 12)
            y = height - 70
            for key, value in data.items():
                if isinstance(value, dict):
                    c.drawString(50, y, f"{key.replace('_', ' ').title()}:")
                    y -= 20
                    for subkey, subvalue in value.items():
                        c.drawString(70, y, f"{subkey}: {subvalue:.2f}")
                        y -= 20
                else:
                    c.drawString(50, y, f"{key.replace('_', ' ').title()}: {value:.2f}")
                    y -= 20

        # Visualizations
        for title, html in report['visualizations'].items():
            c.showPage()
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, height - 50, title.replace('_', ' ').title())
            # Here you would convert the HTML to an image and add it to the PDF
            # This is a simplified placeholder:
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 70, "Visualization placeholder")

        c.save()

    async def run_test(self):
        # Пример использования
        user_id = 1
        start_date = "2023-01-01"
        end_date = "2023-12-31"
        
        report = await self.generate_advanced_report(user_id, start_date, end_date)
        
        print("Advanced Report Generated:")
        print(json.dumps(report, indent=2))
        
        print(f"PDF report saved as: report_{user_id}_{start_date}_{end_date}.pdf")

if __name__ == "__main__":
    # Создаем экземпляр DatabaseManager (предполагается, что у вас есть этот класс)
    db_manager = DatabaseManager("your_database_url_here")
    
    # Создаем экземпляр AdvancedReporting
    advanced_reporting = AdvancedReporting(db_manager)
    
    # Запускаем тест
    asyncio.run(advanced_reporting.run_test())