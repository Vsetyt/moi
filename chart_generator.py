import matplotlib.pyplot as plt
import io
import pandas as pd

class ChartGenerator:
    @staticmethod
    def generate_profit_chart(trade_history: pd.DataFrame) -> io.BytesIO:
        plt.figure(figsize=(10, 6))
        plt.plot(trade_history['timestamp'], trade_history['cumulative_profit'])
        plt.title('Кривая доходности')
        plt.xlabel('Время')
        plt.ylabel('Прибыль (USDT)')
        plt.grid(True)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        
        return buf

    @staticmethod
    def generate_trade_distribution_chart(trade_history: pd.DataFrame) -> io.BytesIO:
        plt.figure(figsize=(10, 6))
        trade_history['profit'].hist(bins=50)
        plt.title('Распределение прибыли по сделкам')
        plt.xlabel('Прибыль (USDT)')
        plt.ylabel('Количество сделок')
        plt.grid(True)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()
        
        return buf