"""
FeatureEngineering Module - Crée les indicateurs techniques pour le trading
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split


class FeatureEngineering:
    """Génère les features techniquess pour le modèle ML"""
    
    @staticmethod
    def add_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
        """
        Ajoute les indicateurs techniques à un DataFrame OHLCV
        
        Args:
            data: DataFrame avec colonnes ['Open', 'High', 'Low', 'Close', 'Volume']
        
        Returns:
            DataFrame enrichi avec 25+ indicateurs techniques
        """
        df = data.copy()
        
        # Moyennes Mobiles Simples (SMA)
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_10'] = df['Close'].rolling(window=10).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        # Moyennes Mobiles Exponentielles (EMA)
        df['EMA_12'] = df['Close'].ewm(span=12).mean()
        df['EMA_26'] = df['Close'].ewm(span=26).mean()
        
        # MACD (Moving Average Convergence Divergence)
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Hist'] = df['MACD'] - df['Signal']
        
        # Bollinger Bands
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        df['BB_Std'] = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * 2)
        df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * 2)
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
        
        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ADX (Average Directional Index)
        df['H-L'] = df['High'] - df['Low']
        df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
        df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        df['ATR'] = df['TR'].rolling(14).mean()
        df['+DM'] = ((df['High'].diff() > df['Low'].diff().abs()) & (df['High'].diff() > 0)).astype(int) * df['High'].diff()
        df['-DM'] = ((df['Low'].diff().abs() > df['High'].diff()) & (df['Low'].diff() < 0)).astype(int) * df['Low'].diff().abs()
        df['+DI'] = 100 * (df['+DM'].rolling(14).mean() / df['ATR'])
        df['-DI'] = 100 * (df['-DM'].rolling(14).mean() / df['ATR'])
        df['ADX'] = abs(df['+DI'] - df['-DI']).rolling(14).mean()
        
        # Stochastic Oscil lator
        df['L14'] = df['Low'].rolling(window=14).min()
        df['H14'] = df['High'].rolling(window=14).max()
        df['Stoch_K'] = 100 * (df['Close'] - df['L14']) / (df['H14'] - df['L14'])
        df['Stoch_D'] = df['Stoch_K'].rolling(window=3).mean()
        
        # Volume Indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # Price Change
        df['Price_Change_1d'] = df['Close'].pct_change(1) * 100
        df['Price_Change_5d'] = df['Close'].pct_change(5) * 100
        df['Price_Change_20d'] = df['Close'].pct_change(20) * 100
        
        # CCI (Commodity Channel Index)
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        cci_sma = tp.rolling(window=20).mean()
        cci_mad = tp.rolling(window=20).apply(lambda x: np.mean(np.abs(x - x.mean())))
        df['CCI'] = (tp - cci_sma) / (0.015 * cci_mad)
        
        # ROC (Rate of Change)
        df['ROC'] = ((df['Close'] - df['Close'].shift(12)) / df['Close'].shift(12)) * 100
        
        # OBV (On Balance Volume)
        df['OBV'] = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
        
        # Williams %R
        df['R%'] = -100 * (df['H14'] - df['Close']) / (df['H14'] - df['L14'])
        
        # Supprimer les colonnes intermédiaires non nécessaires
        cols_to_drop = ['H-L', 'H-PC', 'L-PC', 'TR', '+DM', '-DM', 'L14', 'H14']
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
        
        return df
    
    @staticmethod
    def create_target_variable(data: pd.DataFrame, prediction_window: int = 5) -> pd.Series:
        """
        Crée la variable cible (Target) - 1 si prix monte dans les X jours, 0 sinon
        
        Args:
            data: DataFrame avec colonne 'Close'
            prediction_window: Nombre de jours à l'avance pour la prédiction
        
        Returns:
            Series avec 1 (achat/montée) ou 0 (vente/baisse)
        """
        future_return = data['Close'].shift(-prediction_window) - data['Close']
        target = (future_return > 0).astype(int)
        return target
    
    @staticmethod
    def prepare_training_data(data: pd.DataFrame, test_size: float = 0.2):
        """
        Prépare les données pour l'entraînement du modèle ML
        
        Args:
            data: DataFrame avec indicateurs et target
            test_size: Proportion de test (0.2 = 20% test, 80% train)
        
        Returns:
            X_train, X_test, y_train, y_test, scaler
        """
        # Supprimer les NaN
        data = data.dropna()
        
        # Séparer features et target
        feature_cols = [c for c in data.columns if c not in ['Close', 'Open', 'High', 'Low', 'Volume', 'Target', 'Date']]
        X = data[feature_cols]
        y = data['Target']
        
        # Split train/test (chronologique - important pour séries temporelles)
        split_idx = int(len(X) * (1 - test_size))
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        # Normaliser
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Convertir en DataFrame pour garder les index
        X_train = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
        X_test = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)
        
        # Reset indices pour matching avec dates
        y_train = y_train.reset_index(drop=True)
        y_test = y_test.reset_index(drop=True)
        X_train = X_train.reset_index(drop=True)
        X_test = X_test.reset_index(drop=True)
        
        return X_train, X_test, y_train, y_test, scaler
