"""
Test rapide des 4 tickers avec les améliorations
"""
import sys
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    from data_fetcher import DataFetcher
    from feature_engineering import FeatureEngineering
    from trading_model import TradingModel
    from backtest_engine import BacktestEngine
    import pandas as pd
    
    print("=" * 80)
    print("COMPARAISON MULTI-TICKERS AVEC AMÉLIORATIONS (Stop Loss, Take Profit, Filter)")
    print("=" * 80)
    
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
    results = []
    
    for ticker in tickers:
        print(f"\nTest {ticker}...")
        try:
            # Récupérer les données
            fetcher = DataFetcher()
            data = fetcher.fetch_stock_data(ticker, start_date='2022-01-01')
            
            # Features
            fe = FeatureEngineering()
            data = fe.add_technical_indicators(data)
            data['Target'] = fe.create_target_variable(data)
            
            # Train/Test
            X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(data, test_size=0.2)
            
            # Modèle
            model = TradingModel()
            model.train(X_train, y_train)
            
            # Backtest AVEC améliorations
            predictions = model.predict(X_test)
            engine = BacktestEngine(initial_capital=10000, position_size_pct=0.95,
                                   stop_loss_pct=-2.0, take_profit_pct=5.0, use_trend_filter=True)
            report = engine.run_backtest(data, model, X_test, X_test.index, predictions)
            
            results.append({
                'Ticker': ticker,
                'Rendement': f"{report['total_return_pct']:.2f}%",
                'Trades': report['total_trades'],
                'Win Rate': f"{report['win_rate']:.1f}%",
                'Drawdown': f"{report['max_drawdown']:.2f}%"
            })
            
            print(f"  -> Rendement: {report['total_return_pct']:.2f}% | Trades: {report['total_trades']} | Win Rate: {report['win_rate']:.1f}%")
            
        except Exception as e:
            print(f"  Erreur: {str(e)}")
    
    # Résumé
    print("\n" + "=" * 80)
    print("RÉSUMÉ")
    print("=" * 80)
    results_df = pd.DataFrame(results)
    print(results_df.to_string(index=False))
    
    # Statistiques
    rendements = [float(r['Rendement'].rstrip('%')) for r in results]
    print(f"\nRendement moyen: {sum(rendements)/len(rendements):.2f}%")
    print(f"Rendement total tickers: {sum(rendements):.2f}%")
    
except Exception as e:
    print(f"ERREUR: {e}")
    import traceback
    traceback.print_exc()
