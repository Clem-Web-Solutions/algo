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
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle'].replace(0, np.nan)
        _bb_range = (df['BB_Upper'] - df['BB_Lower']).replace(0, np.nan)
        df['BB_Position'] = (df['Close'] - df['BB_Lower']) / _bb_range
        
        # RSI (Relative Strength Index) — formule Wilder standard (EWM alpha=1/14)
        # La moyenne simple rolling est incorrecte : elle sur-réagit aux données récentes
        delta = df['Close'].diff()
        gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
        loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
        rs = gain / loss.replace(0, np.nan)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ADX (Average Directional Index) — formule standard Wilder
        df['H-L'] = df['High'] - df['Low']
        df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
        df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        df['ATR'] = df['TR'].rolling(14).mean()
        df['+DM'] = ((df['High'].diff() > df['Low'].diff().abs()) & (df['High'].diff() > 0)).astype(int) * df['High'].diff()
        df['-DM'] = ((df['Low'].diff().abs() > df['High'].diff()) & (df['Low'].diff() < 0)).astype(int) * df['Low'].diff().abs()
        df['+DI'] = 100 * (df['+DM'].rolling(14).mean() / df['ATR'].replace(0, np.nan))
        df['-DI'] = 100 * (df['-DM'].rolling(14).mean() / df['ATR'].replace(0, np.nan))
        # DX = 100 * |+DI - -DI| / (+DI + -DI)  puis ADX = EMA(DX, 14) — formule Wilder correcte
        _di_sum = (df['+DI'] + df['-DI']).replace(0, np.nan)
        _dx = 100 * (df['+DI'] - df['-DI']).abs() / _di_sum
        df['ADX'] = _dx.rolling(14).mean()
        
        # Stochastic Oscillator (noms harmonisés avec signal_generator)
        df['L14'] = df['Low'].rolling(window=14).min()
        df['H14'] = df['High'].rolling(window=14).max()
        _stoch_range = (df['H14'] - df['L14']).replace(0, np.nan)  # Protection H14==L14
        df['STOCH_K'] = 100 * (df['Close'] - df['L14']) / _stoch_range
        df['STOCH_D'] = df['STOCH_K'].rolling(window=3).mean()

        # Volume Indicators (nom harmonisé avec signal_generator)
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_SMA_Ratio'] = df['Volume'] / df['Volume_SMA']
        
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
        
        # OBV (On Balance Volume) — normalisé en z-score roulant 20j
        # L'OBV brut est un cumsum dont la valeur absolue dépend de la date de début
        # (ex: fenêtre 2022 → OBV ≈ -33M ; fenêtre 2023 → OBV ≈ +5M pour le même ticker)
        # Le z-score roulant capture le momentum relatif sans dépendance à l'origine
        _obv_raw = (np.sign(df['Close'].diff()) * df['Volume']).fillna(0).cumsum()
        _obv_sma = _obv_raw.rolling(20).mean()
        _obv_std = _obv_raw.rolling(20).std().replace(0, np.nan)
        df['OBV'] = (_obv_raw - _obv_sma) / _obv_std  # z-score roulant (stable cross-cycle)
        
        # Williams %R
        df['R%'] = -100 * (df['H14'] - df['Close']) / (df['H14'] - df['L14'])

        # Awesome Oscillator (AO) — demandé par signal_generator
        # AO = SMA(médiane, 5) - SMA(médiane, 34)
        median_price = (df['High'] + df['Low']) / 2
        df['AO'] = median_price.rolling(window=5).mean() - median_price.rolling(window=34).mean()

        # ---------------------------------------------------------------
        # Features normalisées (price-invariant) pour MACD, ATR, AO
        # ---------------------------------------------------------------
        # MACD brut = EMA12 - EMA26 : sa magnitude est proportionnelle au
        # niveau de prix absolu → non comparable entre TSLA ($250) et AAPL ($180).
        # Solution: diviser par ATR (unité de volatilité locale) pour obtenir
        # des features dimensionnellement homogènes cross-ticker.
        _atr_safe = df['ATR'].replace(0, np.nan)
        df['MACD_ATR']      = df['MACD']      / _atr_safe  # MACD en unités ATR
        df['MACD_Hist_ATR'] = df['MACD_Hist'] / _atr_safe  # Histogramme en unités ATR
        df['ATR_pct']       = df['ATR']        / df['Close'].replace(0, np.nan) * 100  # ATR en % du cours
        df['AO_ATR']        = df['AO']         / _atr_safe  # AO en unités ATR
        # Volatilité annualisée explicite — donne au modèle une conscience du régime de vol
        df['Volatility_20d'] = df['Close'].pct_change().rolling(20).std() * np.sqrt(252) * 100

        # Ratios SMA/EMA relatifs au prix — invariants au niveau de prix absolu
        # Remplacent les SMA/EMA brutes dans les features ML (voir prepare_training_data)
        # ex: SMA_5_r = Close/SMA_5 - 1  →  +0.02 = 2% au-dessus de la SMA_5
        for period, col in [(5, 'SMA_5'), (10, 'SMA_10'), (20, 'SMA_20'),
                            (50, 'SMA_50'), (200, 'SMA_200')]:
            df[f'{col}_r'] = df['Close'] / df[col].replace(0, np.nan) - 1
        df['EMA_12_r'] = df['Close'] / df['EMA_12'].replace(0, np.nan) - 1
        df['EMA_26_r'] = df['Close'] / df['EMA_26'].replace(0, np.nan) - 1

        # Supprimer les colonnes intermédiaires non nécessaires
        cols_to_drop = ['H-L', 'H-PC', 'L-PC', 'TR', '+DM', '-DM', 'L14', 'H14']
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
        
        return df
    
    @staticmethod
    def create_target_variable(
        data: pd.DataFrame,
        prediction_window: int = 5,
        min_return_pct: float = 0.3,
    ) -> pd.Series:
        """
        Crée la variable cible (Target) - 1 si le prix monte d'au moins min_return_pct%
        dans les prediction_window jours, 0 sinon.

        Le seuil min_return_pct (défaut 0.3%) filtre les micro-mouvements (<0.3%)
        qui n'apportent pas de valeur réelle après frais et slippage.
        Avant ce fix: (future_return > 0) générait du signal même pour +0.01%,
        polluant la target avec du bruit pur.

        Args:
            data             : DataFrame avec colonne 'Close'
            prediction_window: Horizon de prédiction en jours
            min_return_pct   : Seuil minimum de hausse en % pour label=1 (défaut 0.3%)

        Returns:
            Series avec 1 (hausse significative prévue) ou 0 sinon
        """
        future_return_pct = (
            data['Close'].shift(-prediction_window) / data['Close'].replace(0, np.nan) - 1
        ) * 100
        target = (future_return_pct > min_return_pct).astype(int)
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
        
        # Colonnes exclues des features ML :
        # - OHLCV bruts (non relativisés)
        # - SMA/EMA absolues : remplacées par les ratios *_r (invariants au niveau de prix)
        # - BB_Middle/Std/Upper/Lower absolus : redondants avec BB_Width et BB_Position
        # - Volume_SMA absolu : redondant avec Volume_SMA_Ratio
        # - MACD/Signal/MACD_Hist/ATR/AO absolus : remplacés par versions normalisées
        #   (MACD_ATR, MACD_Hist_ATR, ATR_pct, AO_ATR) — non comparables cross-ticker
        _excluded = {
            'Close', 'Open', 'High', 'Low', 'Volume', 'Target', 'Date',
            # Niveaux de prix absolus — remplacés par les ratios *_r
            'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50', 'SMA_200',
            'EMA_12', 'EMA_26',
            # Bandes de Bollinger absolues — BB_Width et BB_Position suffisent
            'BB_Middle', 'BB_Std', 'BB_Upper', 'BB_Lower',
            # Volume absolu — Volume_SMA_Ratio est suffisant
            'Volume_SMA',
            # MACD/Signal/ATR/AO absolus (proportionnels au prix) —
            # remplacés par MACD_ATR, MACD_Hist_ATR, ATR_pct, AO_ATR (Iter 5)
            'MACD', 'Signal', 'MACD_Hist', 'ATR', 'AO',
        }
        feature_cols = [c for c in data.columns if c not in _excluded]
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
        
        # Convertir en DataFrame en preservant l'index datetime (critique pour le backtest)
        X_train = pd.DataFrame(X_train_scaled, columns=X_train.columns, index=X_train.index)
        X_test = pd.DataFrame(X_test_scaled, columns=X_test.columns, index=X_test.index)

        # Aligner y sur le meme index que X (sans reset pour conserver les dates)
        y_train = y_train.loc[X_train.index]
        y_test = y_test.loc[X_test.index]

        return X_train, X_test, y_train, y_test, scaler
