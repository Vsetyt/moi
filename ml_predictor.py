import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from typing import List, Dict
import joblib
import logging

logger = logging.getLogger(__name__)

class MLPredictor:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()

    def prepare_data(self, historical_data: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(historical_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        # Создаем дополнительные признаки
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['volume_change'] = df['volume'].pct_change()
        df['price_change'] = df['price'].pct_change()
        
        # Удаляем строки с NaN значениями
        df.dropna(inplace=True)
        
        return df

    def train(self, historical_data: List[Dict]):
        df = self.prepare_data(historical_data)
        
        features = ['hour', 'day_of_week', 'volume', 'volume_change', 'price', 'price_change']
        X = df[features]
        y = df['profit']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        self.model.fit(X_train_scaled, y_train)
        
        score = self.model.score(X_test_scaled, y_test)
        logger.info(f"Model R-squared score: {score}")

    def predict(self, current_data: Dict) -> float:
        df = pd.DataFrame([current_data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        
        features = ['hour', 'day_of_week', 'volume', 'price']
        X = df[features]
        
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)
        return prediction[0]

    def save_model(self, filename: str):
        joblib.dump((self.model, self.scaler), filename)

    def load_model(self, filename: str):
        self.model, self.scaler = joblib.load(filename)