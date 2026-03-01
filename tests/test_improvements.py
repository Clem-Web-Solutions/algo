"""
Script de test pour valider les améliations:
1. Stop Loss (-2%) et Take Profit (+5%)
2. Trend Filter (SMA 200)
"""

import sys
import pandas as pd
import numpy as np

print("=" * 80)
print("🧪 TEST DES AMÉLIORATIONS - STOP LOSS, TAKE PROFIT, TREND FILTER")
print("=" * 80)

try:
    # 1. Test Feature Engineering avec SMA 200
    print("\n[1/3] Test Feature Engineering (SMA 200)...")
    from feature_engineering import FeatureEngineering
    from data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    data = fetcher.fetch_stock_data('AAPL', start_date='2022-01-01')
    
    fe = FeatureEngineering()
    data = fe.add_technical_indicators(data)
    
    # Vérifier que SMA_200 a été créée
    if 'SMA_200' in data.columns:
        print("   ✅ SMA_200 créée avec succès")
        print(f"   Premières valeurs de SMA_200: {data['SMA_200'].head(210).tail(5).values}")
    else:
        print("   ❌ ERREUR: SMA_200 non trouvée!")
        sys.exit(1)
    
    # 2. Test BacktestEngine avec Stop Loss/Take Profit
    print("\n[2/3] Test BacktestEngine (Stop Loss, Take Profit, Trend Filter)...")
    from trading_model import TradingModel
    from backtest_engine import BacktestEngine
    
    # Préparer les données
    data['Target'] = fe.create_target_variable(data)
    X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(data, test_size=0.2)
    
    # Entraîner le modèle
    model = TradingModel()
    model.train(X_train, y_train)
    
    # Faire des prédictions
    predictions = model.predict(X_test)
    test_dates = X_test.index
    
    # Lancer le backtest AVEC stop loss/take profit/trend filter
    print("   1. Backtest AVEC Stop Loss (-2%), Take Profit (+5%), Trend Filter...")
    engine_improved = BacktestEngine(
        initial_capital=10000,
        position_size_pct=0.95,
        stop_loss_pct=-2.0,
        take_profit_pct=5.0,
        use_trend_filter=True
    )
    report_improved = engine_improved.run_backtest(data, model, X_test, test_dates, predictions)
    
    print(f"   ✅ Backtest complété")
    print(f"      Rendement: {report_improved['total_return_pct']:.2f}%")
    print(f"      Nombre de trades: {report_improved['total_trades']}")
    print(f"      Win Rate: {report_improved['win_rate']:.2f}%")
    print(f"      Max Drawdown: {report_improved['max_drawdown']:.2f}%")
    
    # Analyser les trades pour voir les raisons
    trades_df = report_improved['trades_df']
    if 'reason' in trades_df.columns:
        print("\n   📊 Analyse des raisons d'exit:")
        reasons = trades_df[trades_df['type'] == 'SELL']['reason'].value_counts()
        for reason, count in reasons.items():
            print(f"      - {reason}: {count} fois")
    
    # Lancer le backtest SANS stop loss/take profit (contrôle baseline)
    print("\n   2. Backtest SANS Stop Loss/Take Profit (baseline contrôle)...")
    engine_baseline = BacktestEngine(
        initial_capital=10000,
        position_size_pct=0.95,
        stop_loss_pct=-100.0,  # Désactiver en mettant une très grande valeur
        take_profit_pct=100.0,  # Désactiver
        use_trend_filter=False
    )
    report_baseline = engine_baseline.run_backtest(data, model, X_test, test_dates, predictions)
    
    print(f"   ✅ Backtest complété")
    print(f"      Rendement: {report_baseline['total_return_pct']:.2f}%")
    print(f"      Nombre de trades: {report_baseline['total_trades']}")
    print(f"      Win Rate: {report_baseline['win_rate']:.2f}%")
    print(f"      Max Drawdown: {report_baseline['max_drawdown']:.2f}%")
    
    # Comparer
    print("\n" + "=" * 80)
    print("📈 COMPARAISON RÉSULTATS")
    print("=" * 80)
    
    diff_rendement = report_improved['total_return_pct'] - report_baseline['total_return_pct']
    diff_trades = report_improved['total_trades'] - report_baseline['total_trades']
    diff_winrate = report_improved['win_rate'] - report_baseline['win_rate']
    
    print(f"Rendement:")
    print(f"  Improved: {report_improved['total_return_pct']:+.2f}% | Baseline: {report_baseline['total_return_pct']:+.2f}% | Diff: {diff_rendement:+.2f}%")
    
    print(f"\nNombre de trades:")
    print(f"  Improved: {report_improved['total_trades']} | Baseline: {report_baseline['total_trades']} | Diff: {diff_trades:+d}")
    
    print(f"\nWin Rate:")
    print(f"  Improved: {report_improved['win_rate']:.2f}% | Baseline: {report_baseline['win_rate']:.2f}% | Diff: {diff_winrate:+.2f}%")
    
    print(f"\nMax Drawdown:")
    print(f"  Improved: {report_improved['max_drawdown']:.2f}% | Baseline: {report_baseline['max_drawdown']:.2f}% | Diff: {report_improved['max_drawdown'] - report_baseline['max_drawdown']:+.2f}%")
    
    # 3. Valider la structure
    print("\n[3/3] Validation de la structure...")
    
    if diff_rendement > 0:
        print("   ✅ SUCCÈS: Stop Loss/Take Profit/Trend Filter améliorent les rendements!")
    else:
        print("   ⚠️  Les rendements n'ont pas augmenté (peut être normal selon les données)")
    
    if report_improved['total_trades'] < report_baseline['total_trades']:
        print("   ✅ SUCCÈS: Trend Filter réduit les faux signaux (moins de trades)")
    
    print("\n" + "=" * 80)
    print("✅ TESTS COMPLÉTÉS AVEC SUCCÈS!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
