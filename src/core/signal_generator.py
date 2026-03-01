"""
Signal Generator - Cœur du système de live trading ÉTAPE 25
=============================================================

Génère les signaux BUY/SELL en temps réel:
1. Charge les données du marché
2. Génère les indicateurs techniques (features)
3. Détecte le régime de marché (BULL/BEAR/SIDEWAYS)
4. Utilise le modèle ML entraîné pour prédire
5. Retourne signal avec confiance

Utilisation:
    python src/core/signal_generator.py --mode=live --ticker=AAPL
"""

import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Setup paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src' / 'core'))
sys.path.insert(0, str(project_root / 'src' / 'strategies'))

from feature_engineering import FeatureEngineering
from market_regime_detector import MarketRegimeDetector
from trading_model import TradingModel
from data_fetcher import DataFetcher
from config import MODEL_CONFIG, DEFAULT_TICKERS
import joblib


class SignalGenerator:
    """Génère les signaux de trading en temps réel"""
    
    def __init__(self, ticker='AAPL', use_model=True):
        """
        Initialise le générateur de signaux
        
        Args:
            ticker: Code action (AAPL, MSFT, GOOGL, TSLA)
            use_model: Utiliser le modèle ML (True pour live trading)
        """
        self.ticker = ticker
        self.use_model = use_model
        self.model = None
        self.model_path = project_root / 'models' / f'model_{ticker}_gb.pkl'
        self.feature_eng = FeatureEngineering()
        self.regime_detector = MarketRegimeDetector()
        self.data_fetcher = DataFetcher()
        
        # Charger le modèle s'il existe
        if use_model and self.model_path.exists():
            try:
                self.model = joblib.load(str(self.model_path))
                print(f"[OK] Modele charge: {self.model_path.name}")
            except Exception as e:
                print(f"[WARNING] Erreur chargement modele: {e}")
                self.model = None
        
    def fetch_live_data(self, lookback_days=250):
        """
        Charge les données récentes pour générer les signaux
        
        Args:
            lookback_days: Nombre de jours historiques à charger
        
        Returns:
            DataFrame avec données OHLCV
        """
        try:
            data = self.data_fetcher.fetch_stock_data(
                ticker=self.ticker,
                start_date=None,
                end_date=None
            )
            
            if data is None or len(data) == 0:
                print(f"[ERROR] Pas de donnees pour {self.ticker}")
                return None
            
            # Garder les lookback_days derniers jours + les jours manquants
            data = data.tail(lookback_days)
            return data
            
        except Exception as e:
            print(f"[ERROR] Erreur fetch donnees: {e}")
            return None
    
    def generate_signal(self, data=None):
        """
        Génère un signal de trading à partir des données
        
        Args:
            data: DataFrame OHLCV. Si None, fetch les données live
        
        Returns:
            Dict avec:
                - signal: 'BUY', 'SELL', ou 'HOLD'
                - confidence: Float 0-1
                - regime: 'BULL', 'BEAR', 'SIDEWAYS'
                - probability: Float - prob du modèle
                - timestamp: datetime
        """
        # 1. Charger les données si nécessaire
        if data is None:
            data = self.fetch_live_data()
        
        if data is None or len(data) < 50:
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'regime': 'UNKNOWN',
                'probability': 0.5,
                'timestamp': datetime.now(),
                'error': 'Pas assez de données'
            }
        
        try:
            # 2. Générer les features techniques
            data_with_features = self.feature_eng.add_technical_indicators(data.copy())
            
            # 3. Détecter le régime de marché
            regime_info = self.regime_detector.detect_regime(
                data_with_features,
                lookback_days=60,
                use_adaptive_sma=True
            )
            regime = regime_info.get('regime', 'UNKNOWN')
            regime_confidence = regime_info.get('confidence', 0.0)
            
            # 4. Préparer les features pour le modèle
            required_features = [
                'SMA_5', 'SMA_10', 'SMA_20', 'SMA_50', 'SMA_200',
                'EMA_12', 'EMA_26', 'MACD', 'Signal', 'MACD_Hist',
                'RSI', 'STOCH_K', 'STOCH_D', 'ATR', 'ADX',
                'AO', 'CCI', 'BB_Position', 'Volume_SMA_Ratio'
            ]
            
            # Vérifier que les features existent
            available_features = [f for f in required_features if f in data_with_features.columns]
            
            if len(available_features) < 10:
                return {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'regime': regime,
                    'probability': 0.5,
                    'timestamp': datetime.now(),
                    'error': f'Features insuffisantes: {len(available_features)}/{len(required_features)}'
                }
            
            # 5. Obtenir la dernière ligne avec les features
            latest = data_with_features.iloc[-1:][available_features]
            
            # Vérifier les NaN
            if latest.isnull().sum().sum() > 0:
                latest = latest.fillna(method='bfill').fillna(method='ffill')
            
            # 6. Générer le signal avec le modèle si disponible
            if self.model is not None:
                try:
                    # Prédire: 1 = BUY, 0 = SELL
                    prediction = self.model.predict(latest)[0]
                    probability = self.model.predict_proba(latest)[0]
                    
                    # Probabilité du signal préduit
                    signal_prob = probability[prediction]
                    
                except Exception as e:
                    print(f"[WARNING] Erreur prediction modele: {e}")
                    prediction = 0.5
                    signal_prob = 0.5
            else:
                # Sans modèle: utiliser les indicateurs techniques
                prediction = 0.5
                signal_prob = 0.5
            
            # 7. Générer le signal final
            if prediction == 1:  # BUY signal
                signal = 'BUY'
                confidence = signal_prob
            elif prediction == 0:  # SELL signal
                signal = 'SELL'
                confidence = signal_prob
            else:
                signal = 'HOLD'
                confidence = 0.5
            
            # Ajuster confiance selon le régime
            if regime == 'UNKNOWN':
                confidence *= 0.5  # Moins confiant si régime inconnu
            
            return {
                'signal': signal,
                'confidence': min(1.0, max(0.0, confidence)),
                'regime': regime,
                'regime_confidence': regime_confidence,
                'probability': float(signal_prob),
                'timestamp': datetime.now(),
                'ticker': self.ticker,
                'last_price': float(data_with_features['Close'].iloc[-1]),
                'model_used': self.model is not None
            }
            
        except Exception as e:
            print(f"[ERROR] Erreur generation signal: {e}")
            import traceback
            traceback.print_exc()
            return {
                'signal': 'HOLD',
                'confidence': 0.0,
                'regime': 'ERROR',
                'probability': 0.5,
                'timestamp': datetime.now(),
                'error': str(e)
            }
    
    def print_signal(self, signal_data):
        """Affiche le signal de manière lisible"""
        print("\n" + "="*70)
        print(f"SIGNAL DE TRADING - {self.ticker}")
        print("="*70)
        print(f"[TIME] {signal_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"[SIGNAL] Signal: {signal_data['signal']:6} | Confiance: {signal_data['confidence']:.1%}")
        print(f"[REGIME] Regime: {signal_data.get('regime', 'N/A'):10} | Prob: {signal_data['probability']:.2%}")
        print(f"[PRICE] Prix: ${signal_data.get('last_price', 0):.2f}")
        print(f"[MODEL] Modele: {'OUI' if signal_data.get('model_used') else 'NON'}")
        if 'error' in signal_data:
            print(f"[WARNING] Erreur: {signal_data['error']}")
        print("="*70)
        return signal_data
    
    def backtest_signals(self, data, lookback_window=250):
        """
        Backteste la génération de signaux sur des données historiques
        
        Args:
            data: DataFrame historique complet
            lookback_window: Fenêtre pour générer le signal à chaque pas
        
        Returns:
            DataFrame avec signaux pour chaque jour
        """
        signals = []
        
        for i in range(lookback_window, len(data)):
            window_data = data.iloc[i-lookback_window:i].copy()
            signal = self.generate_signal(window_data)
            signal['date'] = data.index[i] if hasattr(data.index, '__getitem__') else i
            signals.append(signal)
        
        return pd.DataFrame(signals)


def main():
    """Fonction principale pour tester le signal generator"""
    parser = argparse.ArgumentParser(description='Signal Generator - Live Trading System')
    parser.add_argument('--mode', choices=['live', 'test'], default='test',
                       help='Mode: live (données réelles) ou test (données historiques)')
    parser.add_argument('--ticker', default='AAPL',
                       help='Ticker à trader (AAPL, MSFT, GOOGL, TSLA)')
    parser.add_argument('--no-model', action='store_true',
                       help='Générer signaux sans modèle ML')
    
    args = parser.parse_args()
    
    print(f"\n[SIGNAL GENERATOR] Mode: {args.mode}")
    print(f"[SIGNAL GENERATOR] Ticker: {args.ticker}")
    print(f"[SIGNAL GENERATOR] Modele ML: {'Non' if args.no_model else 'Oui'}\n")
    
    # Créer le générateur
    sg = SignalGenerator(
        ticker=args.ticker,
        use_model=not args.no_model
    )
    
    if args.mode == 'live':
        # Mode live: charger données récentes et générer signal
        print(f"[DOWNLOAD] Chargement données {args.ticker}...")
        data = sg.fetch_live_data(lookback_days=250)
        
        if data is not None:
            print(f"[OK] {len(data)} jours charges")
            signal = sg.generate_signal(data)
            sg.print_signal(signal)
        else:
            print("[ERROR] Impossible de charger les donnees")
    
    else:
        # Mode test: backtester sur données historiques
        print(f"[DOWNLOAD] Chargement donnees historiques {args.ticker}...")
        fetcher = DataFetcher()
        data = fetcher.fetch_stock_data(ticker=args.ticker, start_date='2023-01-01')
        
        if data is not None and len(data) > 250:
            print(f"[OK] {len(data)} jours charges")
            print(f"[TEST] Backtesting signaux (derniers 50 jours)...")
            
            # Afficher les 10 derniers signaux
            signals = sg.backtest_signals(data, lookback_window=250)
            signals = signals.tail(10)
            
            print(f"\n{'Date':<12} {'Signal':<6} {'Conf':<6} {'Régime':<12} {'Prix':<8}")
            print("-"*50)
            for _, row in signals.iterrows():
                date = str(row['date'])[:10] if 'date' in row else 'N/A'
                sig = row['signal']
                conf = f"{row['confidence']:.1%}"
                regime = row['regime']
                price = f"${row.get('last_price', 0):.2f}"
                print(f"{date:<12} {sig:<6} {conf:<6} {regime:<12} {price:<8}")
        else:
            print("[ERROR] Pas assez de donnees")


if __name__ == '__main__':
    main()
