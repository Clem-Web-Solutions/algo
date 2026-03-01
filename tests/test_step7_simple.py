"""
Test Étape 7 - Version Simplifiée
Teste la détection de régime et stratégie adaptative
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime

from data_fetcher import DataFetcher
from feature_engineering import FeatureEngineering
from trading_model import TradingModel
from backtest_engine import BacktestEngine
from market_regime_detector import MarketRegimeDetector
from adaptive_strategy import AdaptiveStrategy


def run_step7_test():
    """Lance le test simplifié de l'Étape 7"""
    
    print("\n" + "="*80)
    print("🚀 ÉTAPE 7: TEST STRATÉGIE ADAPTATIVE - VERSION SIMPLIFIÉE")
    print("="*80)
    
    ticker = 'AAPL'
    
    # 1. Récupérer les données
    print("\n[1/5] Téléchargement des données...")
    fetcher = DataFetcher()
    try:
        data = fetcher.fetch_stock_data(ticker, start_date='2022-01-01')
    except:
        print("⚠️ Utilisation de données locales")
        data = pd.read_csv(f'data/{ticker}_2022-01-01_2026-02-22.csv', index_col=0, parse_dates=True)
    
    print(f"✅ {len(data)} jours chargés")
    
    # 2. Features
    print("\n[2/5] Création des features...")
    fe = FeatureEngineering()
    data = fe.add_technical_indicators(data)
    
    # 3. Détecteur de régime
    print("\n[3/5] Détection des régimes...")
    regime_history = MarketRegimeDetector.get_regime_history(data)
    regime_stats = MarketRegimeDetector.get_regime_statistics(data)
    
    print(f"\n  📈 Régimes détectés:")
    for regime, pct in regime_stats.get('regime_percentages', {}).items():
        print(f"     {regime:15}: {pct:5.1f}%")
    print(f"\n  Régime prédominant: {regime_stats.get('most_common', 'UNKNOWN')}")
    
    # 4. Modèle
    print("\n[4/5] Entraînement du modèle...")
    data['Target'] = fe.create_target_variable(data, prediction_window=5)
    X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(data)
    
    model = TradingModel(model_type='neural_network')
    model.train(X_train, y_train)
    
    # 5. Backtester
    print("\n[5/5] Backtesting...")
    
    # Stratégie standard
    print("\n  📊 Stratégie STANDARD...")
    engine_standard = BacktestEngine(stop_loss_pct=-2.0, take_profit_pct=5.0, use_trend_filter=True)
    
    result_standard = engine_standard.run_backtest(
        data, model, X_test, X_test.index, model.predict(X_test)
    )
    
    std_return = result_standard.get('total_return', 0)
    
    # Stratégie adaptative (utilise les régimes)
    print("  📊 Stratégie ADAPTATIVE...")
    result_adaptive = run_adaptive_backtest(data, model, X_test, regime_history)
    adap_return = result_adaptive.get('total_return', 0)
    
    # Buy & Hold
    print("  📊 Buy & Hold...")
    bh_return = calculate_buyhold(data, X_test.index)
    
    # Rapport
    print("\n" + "="*80)
    print("📊 RÉSULTATS - ÉTAPE 7")
    print("="*80)
    
    print(f"\nBuy & Hold:          {bh_return:+8.2f}%")
    print(f"Standard (Étape 6):  {std_return:+8.2f}%")
    print(f"Adaptative (NEW):    {adap_return:+8.2f}%")
    
    print(f"\n✅ Amélioration Adaptative vs Standard: {adap_return - std_return:+.2f}%")
    
    # Sauvegarder
    save_results(bh_return, std_return, adap_return, regime_stats, ticker)
    
    print("\n✅ Test Étape 7 complété!")


def run_adaptive_backtest(data, model, X_test, regime_history):
    """Exécute un backtest adaptatif"""
    
    engine = BacktestEngine()
    portfolio_values = [engine.initial_capital]
    cash = engine.initial_capital
    position = 0
    entry_price = None
    trades_count = 0
    
    predictions = model.predict(X_test)
    
    # Itérer sur chaque date de test
    for test_idx, (date, row_idx) in enumerate(zip(X_test.index, range(len(X_test)))):
        if test_idx >= len(predictions):
            break
        
        pred = predictions[test_idx]
        
        # Accéder aux données
        if date not in data.index:
            continue
        
        data_row = data.loc[[date]].iloc[0]  # En tant que Series
        price = float(data_row['Close'].values[0] if hasattr(data_row['Close'], 'values') else data_row['Close'])
        
        # Déterminer le régime
        regime = 'UNKNOWN'
        if len(regime_history) > 0:
            filtered = regime_history[regime_history['date'] <= date]
            if len(filtered) > 0:
                regime = filtered.iloc[-1]['regime']
        
        # Paramètres adaptés
        params = AdaptiveStrategy.get_params_for_regime(regime)
        sl_pct = params['stop_loss_pct'] / 100.0
        tp_pct = params['take_profit_pct'] / 100.0
        
        signal = int(pred)
        
        # Gestion position
        if position > 0:
            pnl_pct = (price - entry_price) / entry_price
            
            if pnl_pct >= tp_pct or pnl_pct <= sl_pct or signal == 0:
                cash += position * price
                position = 0
                trades_count += 1
        
        # Achat
        if signal == 1 and position == 0:
            shares = int(cash * 0.95 / price)
            if shares > 0:
                entry_price = price
                position = shares
                cash -= shares * price
                trades_count += 1
        
        # Portfolio value
        if position > 0:
            current_value = cash + (position * price)
        else:
            current_value = cash
        
        portfolio_values.append(current_value)
    
    # Fermer position finale
    if position > 0 and len(data) > 0:
        final_row = data.iloc[-1]
        final_price = float(final_row['Close'].values[0] if hasattr(final_row['Close'], 'values') else final_row['Close'])
        cash += position * final_price
    
    final_value = cash
    total_return = ((final_value - engine.initial_capital) / engine.initial_capital * 100)
    
    return {
        'final_value': final_value,
        'total_return': total_return,
        'trades': trades_count,
        'portfolio_values': portfolio_values
    }


def calculate_buyhold(data, test_dates):
    """Calcule le rendement buy & hold"""
    if len(test_dates) < 2:
        return 0.0
    
    entry_date = test_dates[0]
    exit_date = test_dates[-1]
    
    entry_price = float(data.loc[entry_date, 'Close'].values[0] if hasattr(data.loc[entry_date, 'Close'], 'values') else data.loc[entry_date, 'Close'])
    exit_price = float(data.loc[exit_date, 'Close'].values[0] if hasattr(data.loc[exit_date, 'Close'], 'values') else data.loc[exit_date, 'Close'])
    
    return ((exit_price - entry_price) / entry_price * 100)


def save_results(bh_return, std_return, adapt_return, regime_stats, ticker):
    """Sauvegarde les résultats"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/step7_results_{ticker}_{timestamp}.txt"
    
    os.makedirs("reports", exist_ok=True)
    
    with open(filename, 'w') as f:
        f.write("="*80 + "\n")
        f.write("RÉSULTATS - ÉTAPE 7: STRATÉGIE ADAPTATIVE\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"Ticker: {ticker}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Résultats:\n")
        f.write("-"*80 + "\n")
        f.write(f"Buy & Hold:           {bh_return:+8.2f}%\n")
        f.write(f"Stratégie Standard:   {std_return:+8.2f}%\n")
        f.write(f"Stratégie Adaptative: {adapt_return:+8.2f}%\n\n")
        
        f.write(f"Amélioration Adaptative vs Standard: {adapt_return - std_return:+.2f}%\n")
        f.write(f"Amélioration Adaptative vs B&H:     {adapt_return - bh_return:+.2f}%\n\n")
        
        f.write("Distribution des régimes:\n")
        f.write("-"*80 + "\n")
        for regime, pct in regime_stats.get('regime_percentages', {}).items():
            f.write(f"  {regime:20}: {pct:6.1f}%\n")
        
        f.write(f"\nRégime prédominant: {regime_stats.get('most_common', 'UNKNOWN')}\n")
    
    print(f"\n✅ Résultats sauvegardés: {filename}")


if __name__ == '__main__':
    run_step7_test()
