"""
Test Étape 7 - Stratégie Adaptative Complète
Teste le système avec détection de régime et stratégie adaptative
"""
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from data_fetcher import DataFetcher
from feature_engineering import FeatureEngineering
from trading_model import TradingModel
from backtest_engine import BacktestEngine
from market_regime_detector import MarketRegimeDetector
from adaptive_strategy import AdaptiveStrategy


class AdaptiveStrategyTester:
    """Teste la stratégie complète avec régimes adaptatifs"""
    
    def __init__(self, ticker='AAPL', data_dir='data'):
        self.ticker = ticker
        self.data_dir = data_dir
        self.fetcher = DataFetcher(data_dir=data_dir)
    
    def run(self, start_date='2022-01-01'):
        """Lance le test complet"""
        
        print("\n" + "="*80)
        print(f"🚀 ÉTAPE 7: TEST STRATÉGIE ADAPTATIVE - {self.ticker}")
        print("="*80)
        
        # 1. Récupérer les données
        print("\n[1/6] Téléchargement des données...")
        try:
            data = self.fetcher.fetch_stock_data(self.ticker, start_date)
        except:
            # Charger données locales
            data = self._load_local_data(self.ticker)
            if data is None:
                print("❌ Impossible de charger les données")
                return
        
        print(f"✅ {len(data)} jours de données chargés")
        
        # 2. Créer les features
        print("\n[2/6] Création des features...")
        fe = FeatureEngineering()
        data = fe.add_technical_indicators(data)
        
        # 3. Détecter les régimes
        print("\n[3/6] Détection des régimes de marché...")
        regime_history = MarketRegimeDetector.get_regime_history(data)
        regime_stats = MarketRegimeDetector.get_regime_statistics(data)
        
        self._display_regime_stats(regime_stats)
        
        # 4. Entraîner le modèle
        print("\n[4/6] Entraînement du modèle...")
        fe = FeatureEngineering()
        
        # Ajouter la target variable
        data['Target'] = fe.create_target_variable(data, prediction_window=5)
        
        # Préparer les données d'entraînement
        X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(data)
        
        model = TradingModel(model_type='neural_network')
        model.train(X_train, y_train)
        
        # Récupérer les données de test pour le backtesting
        test_dates = X_test.index
        test_indices = np.arange(len(X_train), len(X_train) + len(X_test))
        
        # 5. Backtester - Comparaison 3 approches
        print("\n[5/6] Backtesting - 3 approches...")
        
        results = {}
        
        # Approche 1: Standard (ancienne)
        print("\n  📊 Approche 1: Stratégie STANDARD (ancienne)...")
        engine_standard = BacktestEngine(
            stop_loss_pct=-2.0, take_profit_pct=5.0, use_trend_filter=True
        )
        results['standard'] = engine_standard.run_backtest(
            data, model, X_test, test_dates,
            model.model.predict(X_test)
        )
        
        # Approche 2: Adaptative simple
        print("  📊 Approche 2: Stratégie ADAPTATIVE (simple)...")
        results['adaptive_simple'] = self._run_adaptive_simple(
            data, model, X_test, test_dates, regime_history
        )
        
        # Approche 3: Adaptative avancée avec switching
        print("  📊 Approche 3: Stratégie ADAPTATIVE AVANCÉE (avec switching)...")
        results['adaptive_advanced'] = self._run_adaptive_advanced(
            data, model, X_test, test_dates, regime_history
        )
        
        # Buy & Hold
        print("  📊 Approche 4: Buy & Hold (référence)...")
        results['buy_hold'] = self._calculate_buy_hold(data, test_dates)
        
        # 6. Générer le rapport
        print("\n[6/6] Génération du rapport...")
        report = self._generate_report(results, regime_stats, data, test_dates)
        
        self._save_report(report)
        
        print("\n✅ Test complété!")
        return results
    
    def _load_local_data(self, ticker):
        """Charge les données locales disponibles"""
        for file in os.listdir(self.data_dir):
            if ticker in file and file.endswith('.csv'):
                try:
                    return pd.read_csv(os.path.join(self.data_dir, file), index_col=0, parse_dates=True)
                except:
                    continue
        return None
    
    def _display_regime_stats(self, stats):
        """Affiche les statistiques des régimes"""
        
        print(f"\n  📈 Distribution des régimes:")
        if 'regime_percentages' in stats:
            for regime, pct in stats['regime_percentages'].items():
                print(f"     {regime:15} : {pct:5.1f}%")
        print(f"\n  Régime prédominant: {stats.get('most_common', 'UNKNOWN')}")
        print(f"  Confiance moyenne: {stats.get('avg_confidence', 0):.2f}")
    
    def _run_adaptive_simple(self, data, model, X_test, test_dates, regime_history):
        """Stratégie adaptative simple - change les paramètres par régime"""
        
        engine = BacktestEngine()
        portfolio = [engine.initial_capital]
        cash = engine.initial_capital
        position = 0
        entry_price = None
        trades = []
        
        predictions = model.model.predict(X_test)
        
        for idx, (date, pred) in enumerate(zip(test_dates, predictions)):
            if date not in data.index:
                continue
            
            row = data.loc[date]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            price = float(row['Close'])
            
            # Trouver le régime à cette date
            regime_row = regime_history[regime_history['date'] <= date].iloc[-1] if len(regime_history) > 0 else None
            regime = regime_row['regime'] if regime_row is not None else 'UNKNOWN'
            
            # Adapter les paramètres
            params = AdaptiveStrategy.get_params_for_regime(regime)
            sl_pct = params['stop_loss_pct'] / 100.0
            tp_pct = params['take_profit_pct'] / 100.0
            use_filter = params['use_trend_filter']
            
            signal = int(pred)
            
            # Trend filter
            trend_ok = True
            if use_filter and 'SMA_200' in data.columns:
                sma_200_val = row['SMA_200'] if 'SMA_200' in row.index else None
                sma_200_val = float(sma_200_val) if sma_200_val is not None and not pd.isna(sma_200_val) else None
                trend_ok = (price > sma_200_val) if sma_200_val is not None else True
            
            # Gestion position
            if position > 0:
                pnl_pct = (price - entry_price) / entry_price
                
                if pnl_pct >= tp_pct:
                    cash += position * price
                    trades.append({'date': date, 'action': 'SELL', 'reason': 'TP', 'price': price})
                    position = 0
                elif pnl_pct <= sl_pct:
                    cash += position * price
                    trades.append({'date': date, 'action': 'SELL', 'reason': 'SL', 'price': price})
                    position = 0
                elif signal == 0:
                    cash += position * price
                    trades.append({'date': date, 'action': 'SELL', 'reason': 'Signal', 'price': price})
                    position = 0
            
            if signal == 1 and position == 0 and trend_ok:
                shares = int(cash * 0.95 / price)
                if shares > 0:
                    entry_price = price
                    position = shares
                    cash -= shares * price
                    trades.append({'date': date, 'action': 'BUY', 'regime': regime, 'price': price})
            
            if position > 0:
                current_value = cash + (position * price)
            else:
                current_value = cash
            
            portfolio.append(current_value)
        
        if position > 0:
            final_price = float(data.iloc[-1]['Close'])
            cash += position * final_price
        
        return {
            'final_value': cash,
            'total_return': ((cash - engine.initial_capital) / engine.initial_capital * 100),
            'trades': len(trades),
            'portfolio_values': portfolio
        }
    
    def _run_adaptive_advanced(self, data, model, X_test, test_dates, regime_history):
        """Stratégie adaptative avancée - switching intelligent entre stratégies"""
        
        engine = BacktestEngine()
        portfolio = [engine.initial_capital]
        cash = engine.initial_capital
        position = 0
        entry_price = None
        trades = []
        prev_regime = 'UNKNOWN'
        
        predictions = model.model.predict(X_test)
        
        for idx, (date, pred) in enumerate(zip(test_dates, predictions)):
            if date not in data.index:
                continue
            
            row = data.loc[date]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            price = float(row['Close'])
            
            # Déterminer le régime
            regime_row = regime_history[regime_history['date'] <= date].iloc[-1] if len(regime_history) > 0 else None
            regime = regime_row['regime'] if regime_row is not None else 'UNKNOWN'
            confidence = regime_row['confidence'] if regime_row is not None else 0.5
            
            # Logique de switching:
            # - BULL: Mode agressif (peu de filtrages)
            # - BEAR: Mode défensif (beaucoup de filtrages)
            # - Changement de régime: Sortir de position et attendre confirmation
            
            signal = int(pred)
            
            # Détection de changement de régime
            regime_changed = (regime != prev_regime)
            if regime_changed and position > 0:
                # Sortir si le régime change
                cash += position * price
                trades.append({'date': date, 'action': 'SELL', 'reason': f'Regime_Change_{prev_regime}_to_{regime}', 'price': price})
                position = 0
            
            # Appliquer la stratégie selon le régime
            if regime == 'BULL':
                # Mode agressif: peu filtrage, plus de trades
                trend_ok = True
                sl_pct = -0.03  # plus large
                tp_pct = 0.07   # profit plus agressif
                
            elif regime == 'BEAR':
                # Mode défensif: beaucoup filtrage, peu de trades
                trend_ok = False  # Ne pas acheter en bear
                if position > 0:  # Mais sortir rapidement si on est dedans
                    cash += position * price
                    trades.append({'date': date, 'action': 'SELL', 'reason': f'Bear_Regime', 'price': price})
                    position = 0
                sl_pct = -0.01  # très strict
                tp_pct = 0.02
                
            else:  # SIDEWAYS, CONSOLIDATION
                # Mode neutre: filtraging standard
                trend_ok = True
                sl_pct = -0.02
                tp_pct = 0.05
            
            # Gestion position
            if position > 0:
                pnl_pct = (price - entry_price) / entry_price
                
                if pnl_pct >= tp_pct:
                    cash += position * price
                    trades.append({'date': date, 'action': 'SELL', 'reason': 'TP', 'price': price})
                    position = 0
                elif pnl_pct <= sl_pct:
                    cash += position * price
                    trades.append({'date': date, 'action': 'SELL', 'reason': 'SL', 'price': price})
                    position = 0
                elif signal == 0:
                    cash += position * price
                    trades.append({'date': date, 'action': 'SELL', 'reason': 'Signal', 'price': price})
                    position = 0
            
            if signal == 1 and position == 0 and trend_ok and confidence > 0.4:
                shares = int(cash * (0.90 if regime == 'BULL' else 0.80) / price)
                if shares > 0:
                    entry_price = price
                    position = shares
                    cash -= shares * price
                    trades.append({'date': date, 'action': 'BUY', 'regime': regime, 'price': price})
            
            if position > 0:
                current_value = cash + (position * price)
            else:
                current_value = cash
            
            portfolio.append(current_value)
            prev_regime = regime
        
        if position > 0:
            final_price = float(data.iloc[-1]['Close'])
            cash += position * final_price
        
        return {
            'final_value': cash,
            'total_return': ((cash - engine.initial_capital) / engine.initial_capital * 100),
            'trades': len(trades),
            'portfolio_values': portfolio
        }
    
    def _calculate_buy_hold(self, data, test_dates):
        """Calcule stratégie buy & hold"""
        
        if not test_dates or len(test_dates) == 0:
            return {'total_return': 0}
        
        entry_date = test_dates[0]
        exit_date = test_dates[-1]
        
        entry_price = float(data.loc[entry_date, 'Close'])
        exit_price = float(data.loc[exit_date, 'Close'])
        
        return_pct = ((exit_price - entry_price) / entry_price * 100)
        
        return {
            'total_return': return_pct,
            'trades': 2  # 1 buy + 1 sell
        }
    
    def _generate_report(self, results, regime_stats, data, test_dates):
        """Génère le rapport de comparaison"""
        
        report = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'ticker': self.ticker,
            'test_period': f"{test_dates[0].date()} à {test_dates[-1].date()}" if test_dates else "N/A",
            'data_length': len(data),
            'regime_distribution': regime_stats.get('regime_percentages', {}),
            'main_regime': regime_stats.get('most_common', 'UNKNOWN'),
            'results': results
        }
        
        return report
    
    def _save_report(self, report):
        """Sauvegarde le rapport"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/adaptive_strategy_test_{report['ticker']}_{timestamp}.txt"
        
        os.makedirs("reports", exist_ok=True)
        
        with open(filename, 'w') as f:
            f.write("="*80 + "\n")
            f.write("ÉTAPE 7: TEST STRATÉGIE ADAPTATIVE\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Ticker: {report['ticker']}\n")
            f.write(f"Période: {report['test_period']}\n")
            f.write(f"Jours testés: {report['data_length']}\n")
            f.write(f"Régime prédominant: {report['main_regime']}\n\n")
            
            f.write("Distribution des régimes:\n")
            f.write("-"*80 + "\n")
            for regime, pct in report['regime_distribution'].items():
                f.write(f"  {regime:20} : {pct:6.1f}%\n")
            
            f.write("\n" + "="*80 + "\n")
            f.write("RÉSULTATS: COMPARAISON 3 APPROCHES\n")
            f.write("="*80 + "\n\n")
            
            standard_ret = report['results']['standard'].get('total_return', 0)
            adaptive_simple_ret = report['results']['adaptive_simple'].get('total_return', 0)
            adaptive_adv_ret = report['results']['adaptive_advanced'].get('total_return', 0)
            bh_ret = report['results']['buy_hold']['total_return']
            
            f.write(f"Buy & Hold:                 {bh_ret:+8.2f}%\n")
            f.write(f"Standard (Étape 6):         {standard_ret:+8.2f}%\n")
            f.write(f"Adaptative Simple (NEW):    {adaptive_simple_ret:+8.2f}%\n")
            f.write(f"Adaptative Avancée (NEW):   {adaptive_adv_ret:+8.2f}%\n")
            
            f.write("\n" + "-"*80 + "\n")
            f.write("Améliorations vs Standard:\n")
            f.write("-"*80 + "\n")
            f.write(f"Adaptative Simple:   {adaptive_simple_ret - standard_ret:+.2f}%\n")
            f.write(f"Adaptative Avancée:  {adaptive_adv_ret - standard_ret:+.2f}%\n")
            
            f.write("\n" + "-"*80 + "\n")
            f.write("Améliorations vs Buy & Hold:\n")
            f.write("-"*80 + "\n")
            f.write(f"Adaptative Simple:   {adaptive_simple_ret - bh_ret:+.2f}%\n")
            f.write(f"Adaptative Avancée:  {adaptive_adv_ret - bh_ret:+.2f}%\n")
            
            f.write("\n✅ Rapport généré: " + timestamp + "\n")
        
        print(f"\n✅ Rapport sauvegardé: {filename}")


def main():
    """Lance le test"""
    tester = AdaptiveStrategyTester(ticker='AAPL')
    results = tester.run()
    return results


if __name__ == '__main__':
    main()
