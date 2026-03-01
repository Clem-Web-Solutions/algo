"""
Debug script pour identifier le probleme dans test_bear_market_adaptive
"""
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Ajouter les chemins des modules
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(project_root, 'src', 'core'))
sys.path.insert(0, os.path.join(project_root, 'src', 'analysis'))
sys.path.insert(0, os.path.join(project_root, 'src', 'strategies'))

from data_fetcher import DataFetcher
from feature_engineering import FeatureEngineering
from trading_model import TradingModel
from backtest_engine import BacktestEngine
from market_regime_detector import MarketRegimeDetector
from adaptive_strategy import AdaptiveStrategy

def test_2008_scenario():
    """Test le scenario 2008 en detail"""
    print("\n" + "="*80)
    print("[DEBUG] Test du scenario 2008 Financial Crisis")
    print("="*80)
    
    fetcher = DataFetcher()
    fe = FeatureEngineering()
    
    # Telecharger les donnees
    print("\n[1/7] Telechargement des donnees...")
    data = fetcher.fetch_stock_data('SPY', start_date='2007-10-01', end_date='2009-03-01')
    print(f"      [OK] {len(data)} jours de donnees")
    print(f"      Index type: {type(data.index)}")
    print(f"      Columns: {data.columns.tolist()}")
    
    # Calculer Buy & Hold
    print("\n[2/7] Calcul du Buy & Hold...")
    start_price = float(data['Close'].iloc[0])
    end_price = float(data['Close'].iloc[-1])
    bh_return = (end_price / start_price - 1) * 100
    prices = data['Close'].values
    running_max = np.maximum.accumulate(prices)
    drawdown = (prices - running_max) / running_max
    max_dd = float(np.min(drawdown)) * 100
    print(f"      BH Return: {bh_return:+.2f}%")
    print(f"      BH Max DD: {max_dd:.2f}%")
    
    # Preparer les features
    print("\n[3/7] Preparation des features...")
    try:
        data = fe.add_technical_indicators(data)
        print(f"      [OK] Technical indicators ajoutes")
    except Exception as e:
        print(f"      [ERROR] {str(e)}")
        return
    
    try:
        data['Target'] = fe.create_target_variable(data)
        print(f"      [OK] Target variable creee")
    except Exception as e:
        print(f"      [ERROR] {str(e)}")
        return
    
    # Nettoyer les donnees
    print("\n[4/7] Nettoyage des donnees...")
    # Utiliser prepare_training_data qui gere correctement les NaN avec fillna
    X_train_np, X_test_np, y_train, y_test, scaler = fe.prepare_training_data(data, test_size=0.2)
    
    # prepare_training_data retourne DataFrames, donc on peut acceder aux indices
    print(f"      X_train shape: {X_train_np.shape}, X_test shape: {X_test_np.shape}")
    
    if len(X_test_np) < 5:
        print(f"      [ERROR] Pas assez de donnees de test: {len(X_test_np)}")
        return
    
    # Obtenir les indices correspondants
    # X_train et X_test sont des DataFrames apres prepare_training_data
    train_indices = X_train_np.index if hasattr(X_train_np, 'index') else list(range(len(X_train_np)))
    test_indices = X_test_np.index if hasattr(X_test_np, 'index') else list(range(len(X_train_np), len(X_train_np) + len(X_test_np)))
    
    print(f"      Train indices: {len(train_indices)}, Test indices: {len(test_indices)}")
    
    # Preparer X et y
    print("\n[6/7] Preparation de X et y...")
    feature_cols = [c for c in X_train_np.columns 
                  if c not in ['Close', 'Open', 'High', 'Low', 'Volume', 'Target']]
    print(f"      Nombre de features: {len(feature_cols)}")
    print(f"      Features: {feature_cols[:5]}... (affichage des 5 premiers)")
    
    X_train = X_train_np[feature_cols].values if hasattr(X_train_np, 'columns') else X_train_np
    X_test = X_test_np[feature_cols].values if hasattr(X_test_np, 'columns') else X_test_np
    
    # Entrainsner le modele
    print("\n[7/7] Test de l'execution adaptative...")
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.preprocessing import StandardScaler
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
        model.fit(X_train_scaled, y_train)
        print(f"      [OK] Modele entraine")
        
        # Predictions
        predictions = model.predict(X_test_scaled)
        print(f"      [OK] {len(predictions)} predictions generees")
        
        # Essayer d'utiliser les methodes
        print("\n[TEST] Appel de MarketRegimeDetector.get_regime_history()...")
        try:
            regime_history = MarketRegimeDetector.get_regime_history(data)
            print(f"      [OK] regime_history obtenue: {len(regime_history)} rows")
            print(f"      Derniers regimes: {regime_history['regime'].tail().tolist()}")
        except Exception as e:
            print(f"      [ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n[TEST] Appel de MarketRegimeDetector.get_regime_statistics()...")
        try:
            regime_stats = MarketRegimeDetector.get_regime_statistics(data)
            print(f"      [OK] regime_stats obtenues")
            print(f"      Stats: {regime_stats}")
        except Exception as e:
            print(f"      [ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n[TEST] Creation du BacktestEngine...")
        try:
            engine = BacktestEngine(
                initial_capital=10000,
                stop_loss_pct=-2.0,
                take_profit_pct=5.0,
                use_trend_filter=True
            )
            print(f"      [OK] BacktestEngine cree")
        except Exception as e:
            print(f"      [ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n[TEST] Appel de AdaptiveStrategy.adapt_backtest_engine()...")
        try:
            current_regime = 'BEAR'  # Assumons bear market en 2008
            confidence = 0.8
            engine_adapted = AdaptiveStrategy.adapt_backtest_engine(engine, current_regime, confidence)
            print(f"      [OK] Engine adapte")
            print(f"      SL: {engine_adapted.stop_loss_pct*100:.2f}%")
            print(f"      TP: {engine_adapted.take_profit_pct*100:.2f}%")
        except Exception as e:
            print(f"      [ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n[TEST] Appel de engine.run_backtest()...")
        try:
            # Si X_test_np a un index, l'utiliser, sinon générer les dates
            if hasattr(X_test_np, 'index'):
                test_dates = X_test_np.index
            else:
                # Utiliser les derniers indices de data qui correspondent aux test_dates
                test_dates = data.index[len(data)-len(X_test):]
            
            print(f"      test_dates type: {type(test_dates)}")
            print(f"      test_dates length: {len(test_dates)}")
            print(f"      data.index type: {type(data.index)}")
            print(f"      data.index length: {len(data.index)}")
            
            # Verifier si les indices correspondent
            print(f"      Verification des indices...")
            matching = 0
            for d in test_dates:
                if d in data.index:
                    matching += 1
            print(f"      Correspondance: {matching}/{len(test_dates)}")
            
            result = engine_adapted.run_backtest(data, model, X_test_scaled, test_dates, predictions)
            print(f"      [OK] Backtest execute")
            print(f"      Resultats: {result}")
            
        except Exception as e:
            print(f"      [ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
    
    except Exception as e:
        print(f"      [ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_2008_scenario()
