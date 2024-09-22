import pandas as pd
import numpy as np
from typing import Dict, Callable
from dataclasses import dataclass

@dataclass
class Trade:
    entry_time: pd.Timestamp
    entry_price: float
    exit_time: pd.Timestamp = None
    exit_price: float = None
    position_size: float = 0
    pnl: float = 0

class Backtester:
    def __init__(self, data: pd.DataFrame, initial_capital: float = 10000):
        self.data = data
        self.initial_capital = initial_capital

    def run(self, strategy: Callable, params: Dict) -> Dict:
        self.equity = [self.initial_capital]
        self.trades = []
        self.current_position = None

        for i in range(1, len(self.data)):
            signal = strategy(self.data.iloc[:i], params)
            
            if signal != 0 and self.current_position is None:
                self._open_position(signal, self.data.index[i], self.data['close'][i])
            elif signal == 0 and self.current_position is not None:
                self._close_position(self.data.index[i], self.data['close'][i])

            self.equity.append(self._calculate_equity(self.data['close'][i]))

        if self.current_position is not None:
            self._close_position(self.data.index[-1], self.data['close'][-1])

        return self._calculate_metrics()

    def _open_position(self, signal: int, time: pd.Timestamp, price: float):
        position_size = self.equity[-1] * 0.1  # Use 10% of equity for each trade
        self.current_position = Trade(
            entry_time=time,
            entry_price=price,
            position_size=position_size * signal  # Positive for long, negative for short
        )

    def _close_position(self, time: pd.Timestamp, price: float):
        self.current_position.exit_time = time
        self.current_position.exit_price = price
        self.current_position.pnl = (price - self.current_position.entry_price) * abs(self.current_position.position_size)
        self.trades.append(self.current_position)
        self.current_position = None

    def _calculate_equity(self, current_price: float) -> float:
        if self.current_position is None:
            return self.equity[-1]
        unrealized_pnl = (current_price - self.current_position.entry_price) * abs(self.current_position.position_size)
        return self.equity[-1] + unrealized_pnl

    def _calculate_metrics(self) -> Dict:
        returns = pd.Series(self.equity).pct_change().dropna()
        
        total_return = (self.equity[-1] - self.initial_capital) / self.initial_capital
        sharpe_ratio = np.sqrt(252) * returns.mean() / returns.std()
        max_drawdown = (pd.Series(self.equity).cummax() - self.equity).max() / pd.Series(self.equity).cummax().max()
        
        win_rate = sum(trade.pnl > 0 for trade in self.trades) / len(self.trades) if self.trades else 0
        average_win = np.mean([trade.pnl for trade in self.trades if trade.pnl > 0]) if self.trades else 0
        average_loss = np.mean([trade.pnl for trade in self.trades if trade.pnl <= 0]) if self.trades else 0
        
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'average_win': average_win,
            'average_loss': average_loss,
            'trade_count': len(self.trades),
            'equity_curve': self.equity
        }

    def plot_equity_curve(self):
        import matplotlib.pyplot as plt
        plt.figure(figsize=(12, 6))
        plt.plot(self.data.index, self.equity)
        plt.title('Equity Curve')
        plt.xlabel('Date')
        plt.ylabel('Equity')
        plt.show()

    def plot_drawdown(self):
        import matplotlib.pyplot as plt
        equity_series = pd.Series(self.equity, index=self.data.index)
        drawdown = (equity_series.cummax() - equity_series) / equity_series.cummax()
        plt.figure(figsize=(12, 6))
        plt.plot(self.data.index, drawdown)
        plt.title('Drawdown')
        plt.xlabel('Date')
        plt.ylabel('Drawdown')
        plt.show()