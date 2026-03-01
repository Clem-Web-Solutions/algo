"""
Simulation Bear Market - Étape 7.1
Simule une baisse de marché pour valider la stratégie adaptative
"""
import pandas as pd
import numpy as np
from datetime import datetime

from feature_engineering import FeatureEngineering
from trading_model import TradingModel
from backtest_engine import BacktestEngine
from market_regime_detector import MarketRegimeDetector
from adaptive_strategy import AdaptiveStrategy


def create_simulated_bear_market(data, decline_pct=30):
    """
    Crée une version baissière artificielle des données
    pour tester la stratégie en conditions difficiles
    """
    data_bear = data.copy()
    
    # Simuler une baisse progressive
    n_days = len(data_bear)
    decline_factor = 1 - (decline_pct / 100) / n_days  # Baisse graduée
    
    data_bear['Close'] = data_bear['Close'] * (decline_factor ** np.arange(n_days))
    data_bear['Open'] = data_bear['Open'] * (decline_factor ** np.arange(n_days))
    data_bear['High'] = data_bear['High'] * (decline_factor ** np.arange(n_days))
    data_bear['Low'] = data_bear['Low'] * (decline_factor ** np.arange(n_days))
    
    return data_bear


def test_bear_market_simulation():
    """Teste la stratégie en marché simulé baissier"""
    
    print("\n" + "="*80)
    print("🔴 SIMULATION BEAR MARKET - VALIDATION ÉTAPE 7")
    print("="*80)
    
    # Charger données réelles
    print("\n[1/5] Chargement des données...")
    try:
        data_real = pd.read_csv('data/AAPL_2022-01-01_2026-02-22.csv', index_col=0, parse_dates=True)
    except:
        print("❌ Impossible de charger les données")
        return
    
    print(f"✅ {len(data_real)} jours chargés")
    
    # Créer scénarios
    print("\n[2/5] Création de scénarios...")
    scenarios = {
        'Real Bull Market': data_real.copy(),
        'Simulated -20% Decline': create_simulated_bear_market(data_real, 20),
        'Simulated -30% Decline': create_simulated_bear_market(data_real, 30),
        'Simulated -50% Crash': create_simulated_bear_market(data_real, 50),
    }
    
    print(f"✅ {len(scenarios)} scénarios créés")
    
    # Entraîner modèle une fois
    print("\n[3/5] Entraînement du modèle...")
    fe = FeatureEngineering()
    data_train = data_real.copy()
    data_train = fe.add_technical_indicators(data_train)
    data_train['Target'] = fe.create_target_variable(data_train, prediction_window=5)
    
    X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(data_train)
    
    model = TradingModel(model_type='neural_network')
    model.train(X_train, y_train)
    
    print("✅ Modèle entraîné")
    
    # Tester chaque scénario
    print("\n[4/5] Backtesting sur tous les scénarios...")
    
    results = {}
    
    for scenario_name, scenario_data in scenarios.items():
        print(f"\n  {scenario_name}...")
        
        scenario_data = fe.add_technical_indicators(scenario_data)
        
        # Régimes
        regime_history = MarketRegimeDetector.get_regime_history(scenario_data)
        regime_stats = MarketRegimeDetector.get_regime_statistics(scenario_data)
        
        # Stratégie standard
        engine_std = BacktestEngine(stop_loss_pct=-2.0, take_profit_pct=5.0, use_trend_filter=True)
        result_std = engine_std.run_backtest(
            scenario_data, model, X_test, X_test.index, model.predict(X_test)
        )
        std_return = result_std.get('total_return', 0)
        
        # Stratégie adaptative (simplifié)
        result_adapt = simulate_adaptive_backtest(scenario_data, model, X_test, regime_history)
        adapt_return = result_adapt['total_return']
        
        # Buy & Hold
        bh_return = (float(scenario_data.iloc[-1]['Close']) - float(scenario_data.iloc[0]['Close'])) / float(scenario_data.iloc[0]['Close']) * 100
        
        results[scenario_name] = {
            'standard': std_return,
            'adaptive': adapt_return,
            'buyhold': bh_return,
            'main_regime': regime_stats.get('most_common', 'UNKNOWN'),
            'improvement': adapt_return - std_return
        }
        
        print(f"    BH: {bh_return:+7.2f}% | STD: {std_return:+7.2f}% | ADAPT: {adapt_return:+7.2f}% | Δ: {adapt_return - std_return:+6.2f}%")
    
    # Rapport
    print("\n[5/5] Génération du rapport...")
    
    print("\n" + "="*80)
    print("📊 RÉSULTATS SIMULATION BEAR MARKET")
    print("="*80)
    
    for scenario_name, result in results.items():
        print(f"\n{scenario_name}:")
        print(f"  Buy & Hold:    {result['buyhold']:+8.2f}%")
        print(f"  Standard:      {result['standard']:+8.2f}%")
        print(f"  Adaptative:    {result['adaptive']:+8.2f}%")
        print(f"  Amélioration:  {result['improvement']:+8.2f}%")
        print(f"  Régime:        {result['main_regime']}")
    
    # Analyse comparative
    print("\n" + "="*80)
    print("📈 ANALYSE COMPARATIVE")
    print("="*80)
    
    avg_std_return = np.mean([r['standard'] for r in results.values()])
    avg_adapt_return = np.mean([r['adaptive'] for r in results.values()])
    avg_improvement = np.mean([r['improvement'] for r in results.values()])
    
    print(f"\nMoyennes sur tous les scénarios:")
    print(f"  Standard (moyenne):   {avg_std_return:+8.2f}%")
    print(f"  Adaptative (moyenne): {avg_adapt_return:+8.2f}%")
    print(f"  Amélioration moyenne: {avg_improvement:+8.2f}%")
    
    # Vérifier la performance en bear market
    bear_scenarios = {k: v for k, v in results.items() if 'Decline' in k or 'Crash' in k}
    
    if bear_scenarios:
        avg_std_bear = np.mean([r['standard'] for r in bear_scenarios.values()])
        avg_adapt_bear = np.mean([r['adaptive'] for r in bear_scenarios.values()])
        
        print(f"\nEn scénarios BAISSIERS (importantes baisses):")
        print(f"  Standard (moyenne):   {avg_std_bear:+8.2f}%")
        print(f"  Adaptative (moyenne): {avg_adapt_bear:+8.2f}%")
        
        if avg_adapt_bear > avg_std_bear:
            print(f"  ✅ Adaptative GAGNE en baisse: +{avg_adapt_bear - avg_std_bear:.2f}%")
        else:
            print(f"  ⚠️ Standard mieux en baisse: +{avg_std_bear - avg_adapt_bear:.2f}%")
    
    # Sauvegarder le rapport
    save_bear_market_results(results)
    
    print("\n✅ Simulation bear market complétée!")


def simulate_adaptive_backtest(data, model, X_test, regime_history):
    """Backtest adaptatif simplifié"""
    
    engine = BacktestEngine()
    cash = engine.initial_capital
    position = 0
    entry_price = None
    
    predictions = model.predict(X_test)
    
    for idx in range(min(len(X_test), len(predictions))):
        date = X_test.index[idx]
        
        if date not in data.index:
            continue
        
        row = data.loc[[date]].iloc[0]
        price = float(row['Close'].values[0] if hasattr(row['Close'], 'values') else row['Close'])
        pred = predictions[idx]
        
        # Déterminer régime
        regime = 'UNKNOWN'
        if len(regime_history) > 0:
            filtered = regime_history[regime_history['date'] <= date]
            if len(filtered) > 0:
                regime = filtered.iloc[-1]['regime']
        
        # Paramètres adaptatifs
        params = AdaptiveStrategy.get_params_for_regime(regime)
        sl_pct = params['stop_loss_pct'] / 100.0
        tp_pct = params['take_profit_pct'] / 100.0
        
        signal = int(pred)
        
        # Gestion
        if position > 0:
            pnl_pct = (price - entry_price) / entry_price
            if pnl_pct >= tp_pct or pnl_pct <= sl_pct or signal == 0:
                cash += position * price
                position = 0
        
        if signal == 1 and position == 0:
            shares = int(cash * 0.95 / price)
            if shares > 0:
                entry_price = price
                position = shares
                cash -= shares * price
    
    # Fermer
    if position > 0:
        final_price = float(data.iloc[-1]['Close'])
        cash += position * final_price
    
    return {
        'final_value': cash,
        'total_return': ((cash - engine.initial_capital) / engine.initial_capital * 100)
    }


def save_bear_market_results(results):
    """Sauve les résultats"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reports/bear_market_simulation_{timestamp}.txt"
    
    import os
    os.makedirs("reports", exist_ok=True)
    
    with open(filename, 'w') as f:
        f.write("="*80 + "\n")
        f.write("SIMULATION BEAR MARKET - ÉTAPE 7.1\n")
        f.write("="*80 + "\n\n")
        
        f.write("Objectif: Valider que la stratégie adaptative fonctionne bien\n")
        f.write("en conditions difficiles (baisses de marché)\n\n")
        
        f.write("Scénarios testés:\n")
        f.write("-"*80 + "\n")
        
        for scenario, result in results.items():
            f.write(f"\n{scenario}:\n")
            f.write(f"  Buy & Hold:    {result['buyhold']:+8.2f}%\n")
            f.write(f"  Standard:      {result['standard']:+8.2f}%\n")
            f.write(f"  Adaptative:    {result['adaptive']:+8.2f}%\n")
            f.write(f"  Amélioration:  {result['improvement']:+8.2f}%\n")
        
        f.write("\n" + "-"*80 + "\n")
        
        avg_improvement = np.mean([r['improvement'] for r in results.values()])
        f.write(f"\nAmélioration moyenne: {avg_improvement:+.2f}%\n")
        
        if any(r['improvement'] > 0 for r in results.values()):
            f.write("\n✅ Stratégie adaptative AMÉLIORE les résultats dans plusieurs scénarios\n")
        
        f.write("\n" + "="*80 + "\n")
        f.write(f"Généré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"✅ Résultats sauvegardés: {filename}")


if __name__ == '__main__':
    test_bear_market_simulation()
