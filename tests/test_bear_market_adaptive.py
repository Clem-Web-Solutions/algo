"""
Test de la strategie adaptative en bear market - Etape 8
Compare la performance de la strategie adaptative vs Buy & Hold
sur des scenarios de marche baissier historiques
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Ajouter les chemins des modules - Trouver la racine du projet
project_root = os.path.abspath(os.path.dirname(__file__))
while os.path.basename(project_root) != 'algo trading' and project_root != os.path.dirname(project_root):
    project_root = os.path.dirname(project_root)

sys.path.insert(0, os.path.join(project_root, 'src', 'core'))
sys.path.insert(0, os.path.join(project_root, 'src', 'analysis'))
sys.path.insert(0, os.path.join(project_root, 'src', 'strategies'))

# Import des modules du projet
from data_fetcher import DataFetcher
from feature_engineering import FeatureEngineering
from trading_model import TradingModel
from backtest_engine import BacktestEngine
from market_regime_detector import MarketRegimeDetector
from adaptive_strategy import AdaptiveStrategy


class BearMarketTester:
    """Testeur de scenarios de bear market"""
    
    # Scenarios de bear market historiques
    BEAR_SCENARIOS = [
        {
            'name': '2008 Financial Crisis',
            'ticker': 'SPY',
            'start_date': '2007-10-01',
            'end_date': '2009-03-01',
            'description': 'Crash financier mondial - Lehman Brothers'
        },
        {
            'name': '2020 COVID Crash',
            'ticker': 'SPY',
            'start_date': '2020-02-15',
            'end_date': '2020-04-15',
            'description': 'Crash COVID-19 - Marche en chute libre'
        },
        {
            'name': '2022 Tech Selloff',
            'ticker': 'QQQ',
            'start_date': '2022-01-01',
            'end_date': '2022-10-01',
            'description': 'Baisse des techs - Inflation et taux'
        },
        {
            'name': '2018 Q4 Correction',
            'ticker': 'SPY',
            'start_date': '2018-10-01',
            'end_date': '2018-12-31',
            'description': 'Correction Q4 2018 - Taux et guerre commerciale'
        },
        {
            'name': '2011 Debt Crisis',
            'ticker': 'SPY',
            'start_date': '2011-07-01',
            'end_date': '2011-10-01',
            'description': 'Crise de la dette europeenne'
        }
    ]
    
    def __init__(self):
        self.fetcher = DataFetcher()
        self.fe = FeatureEngineering()
        self.results = []
    
    def run_all_tests(self):
        """Execute tous les tests de bear market"""
        print("=" * 80)
        print("[BEAR] TEST DE LA STRATEGIE ADAPTATIVE EN BEAR MARKET")
        print("=" * 80)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Scenarios: {len(self.BEAR_SCENARIOS)} periodes de bear market")
        print("=" * 80)
        
        for scenario in self.BEAR_SCENARIOS:
            self._test_scenario(scenario)
        
        # Generer le rapport final
        self._generate_summary_report()
    
    def _test_scenario(self, scenario):
        """Test un scenario de bear market specifique"""
        print(f"\n{'='*80}")
        print(f"[CHART_DOWN] Scenario: {scenario['name']}")
        print(f"   {scenario['description']}")
        print(f"   Periode: {scenario['start_date']} -> {scenario['end_date']}")
        print(f"   Ticker: {scenario['ticker']}")
        print(f"{'='*80}")
        
        try:
            # Recuperer les donnees
            data = self.fetcher.fetch_stock_data(
                scenario['ticker'],
                start_date=scenario['start_date'],
                end_date=scenario['end_date']
            )
            
            if len(data) < 30:
                print(f"   [WARNING] Pas assez de donnees ({len(data)} jours)")
                return
            
            # Calculer Buy & Hold
            bh_return, bh_max_dd = self._calculate_buy_hold_metrics(data)
            
            print(f"\n   [CHART] BUY & HOLD:")
            print(f"      Rendement: {bh_return:+.2f}%")
            print(f"      Max Drawdown: {bh_max_dd:.2f}%")
            
            # Tester la strategie adaptative
            adaptive_result = self._test_adaptive_strategy(data, scenario)
            
            if adaptive_result:
                print(f"\n   [ROBOT] STRATEGIE ADAPTATIVE:")
                print(f"      Rendement: {adaptive_result['return']:+.2f}%")
                print(f"      Max Drawdown: {adaptive_result['max_dd']:+.2f}%")
                print(f"      Trades: {adaptive_result['trades']}")
                print(f"      Win Rate: {adaptive_result['win_rate']:.1f}%")
                
                # Calculer la protection
                protection = abs(bh_max_dd) - abs(adaptive_result['max_dd'])
                outperformance = adaptive_result['return'] - bh_return
                
                print(f"\n   [SHIELD] PROTECTION:")
                print(f"      Drawdown evite: {protection:.2f}%")
                print(f"      Outperformance: {outperformance:+.2f}%")
                
                # Stocker les resultats
                self.results.append({
                    'scenario': scenario['name'],
                    'ticker': scenario['ticker'],
                    'period': f"{scenario['start_date']} to {scenario['end_date']}",
                    'days': len(data),
                    'bh_return': bh_return,
                    'bh_max_dd': bh_max_dd,
                    'adaptive_return': adaptive_result['return'],
                    'adaptive_max_dd': adaptive_result['max_dd'],
                    'adaptive_trades': adaptive_result['trades'],
                    'adaptive_win_rate': adaptive_result['win_rate'],
                    'protection': protection,
                    'outperformance': outperformance,
                    'regime_distribution': adaptive_result.get('regime_distribution', {})
                })
            else:
                print(f"   [WARNING] Impossible de tester la strategie adaptative")
                
        except Exception as e:
            print(f"   [ERROR] Erreur: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _calculate_buy_hold_metrics(self, data):
        """Calcule les metriques Buy & Hold"""
        start_price = data['Close'].values[0].item() if hasattr(data['Close'].values[0], 'item') else float(data['Close'].values[0])
        end_price = data['Close'].values[-1].item() if hasattr(data['Close'].values[-1], 'item') else float(data['Close'].values[-1])
        total_return = (end_price / start_price - 1) * 100
        
        # Calculer le max drawdown
        prices = data['Close'].values
        running_max = np.maximum.accumulate(prices)
        drawdown = (prices - running_max) / running_max
        max_dd = np.min(drawdown) * 100
        max_dd = max_dd.item() if hasattr(max_dd, 'item') else float(max_dd)
        
        return float(total_return), float(max_dd)
    
    def _test_adaptive_strategy(self, data, scenario):
        """Teste la strategie adaptative sur les donnees"""
        try:
            # Preparer les features
            data = self.fe.add_technical_indicators(data)
            data['Target'] = self.fe.create_target_variable(data)
            
            # Utiliser prepare_training_data pour nettoyer correctement (fillna au lieu de dropna)
            X_train, X_test, y_train, y_test, scaler = self.fe.prepare_training_data(data, test_size=0.2)
            
            if len(X_test) < 5:
                return None
            
            # Entrainer un modele simple (Random Forest pour la rapidite)
            from sklearn.ensemble import RandomForestClassifier
            
            X_train_vals = X_train.values if hasattr(X_train, 'values') else X_train
            X_test_vals = X_test.values if hasattr(X_test, 'values') else X_test
            y_train_vals = y_train.values if hasattr(y_train, 'values') else y_train
            
            model = RandomForestClassifier(n_estimators=50, random_state=42, max_depth=5)
            model.fit(X_train_vals, y_train_vals)
            
            # Predictions
            predictions = model.predict(X_test_vals)
            
            # Backtest adaptatif
            # Recuperer les indices de test correctement
            test_dates = X_test.index if hasattr(X_test, 'index') else data.index[-len(X_test):]
            
            engine = BacktestEngine(
                initial_capital=10000,
                stop_loss_pct=-2.0,
                take_profit_pct=5.0,
                use_trend_filter=True
            )
            
            # Adapter selon le regime
            try:
                regime_history = MarketRegimeDetector.get_regime_history(data)
                current_regime = regime_history['regime'].iloc[-1] if len(regime_history) > 0 else 'UNKNOWN'
                confidence = regime_history['confidence'].iloc[-1] if len(regime_history) > 0 else 0.5
            except:
                current_regime = 'UNKNOWN'
                confidence = 0.5
            
            engine = AdaptiveStrategy.adapt_backtest_engine(engine, current_regime, confidence)
            
            # Executer le backtest
            result = engine.run_backtest(
                data, model, X_test_vals, test_dates, predictions
            )
            
            # Calculer les metriques
            total_return = result['total_return_pct']
            max_dd = result['max_drawdown']
            trades = result['sell_trades']
            win_rate = result['win_rate']
            
            # Recuperer la distribution des regimes
            try:
                regime_stats = MarketRegimeDetector.get_regime_statistics(data)
            except:
                regime_stats = {}
            
            return {
                'return': total_return,
                'max_dd': max_dd,
                'trades': trades,
                'win_rate': win_rate,
                'regime_distribution': regime_stats.get('regime_percentages', {})
            }
            
        except Exception as e:
            print(f"      Erreur dans le test adaptatif: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_summary_report(self):
        """Genere le rapport recapitulatif"""
        if not self.results:
            print("\n[ERROR] Aucun resultat a afficher")
            return
        
        print(f"\n{'='*80}")
        print("[CLIPBOARD] RAPPORT RECAPITULATIF - TESTS BEAR MARKET")
        print(f"{'='*80}")
        
        # Creer DataFrame des resultats
        df = pd.DataFrame(self.results)
        
        # Afficher le tableau comparatif
        print(f"\n{'Scenario':<25} {'Ticker':<6} {'BH Return':<10} {'Adapt Return':<12} {'Protection':<10} {'Outperf':<10}")
        print("-" * 80)
        
        for _, row in df.iterrows():
            print(f"{row['scenario']:<25} {row['ticker']:<6} "
                  f"{row['bh_return']:>+8.2f}% {row['adaptive_return']:>+10.2f}% "
                  f"{row['protection']:>+8.2f}% {row['outperformance']:>+8.2f}%")
        
        # Statistiques globales
        print(f"\n{'='*80}")
        print("[CHART] STATISTIQUES GLOBALES")
        print(f"{'='*80}")
        
        avg_bh_return = df['bh_return'].mean()
        avg_adaptive_return = df['adaptive_return'].mean()
        avg_protection = df['protection'].mean()
        avg_outperformance = df['outperformance'].mean()
        
        print(f"Rendement moyen Buy & Hold:     {avg_bh_return:+.2f}%")
        print(f"Rendement moyen Adaptative:     {avg_adaptive_return:+.2f}%")
        print(f"Protection moyenne (drawdown):  {avg_protection:+.2f}%")
        print(f"Outperformance moyenne:         {avg_outperformance:+.2f}%")
        
        # Compter les victoires
        wins = sum(1 for r in self.results if r['outperformance'] > 0)
        total = len(self.results)
        
        print(f"\n[OK] Scenarios ou l'adaptative gagne: {wins}/{total} ({wins/total*100:.1f}%)")
        
        # Sauvegarder le rapport
        self._save_report(df)
    
    def _save_report(self, df):
        """Sauvegarde le rapport dans un fichier"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/bear_market_test_{timestamp}.txt"
        
        try:
            with open(filename, 'w') as f:
                f.write("=" * 80 + "\n")
                f.write("[BEAR] RAPPORT DE TEST - BEAR MARKET SCENARIOS\n")
                f.write("=" * 80 + "\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Scenarios testes: {len(self.results)}\n\n")
                
                f.write("RESULTATS DETAILLES:\n")
                f.write("-" * 80 + "\n")
                
                for _, row in df.iterrows():
                    f.write(f"\nScenario: {row['scenario']}\n")
                    f.write(f"  Periode: {row['period']} ({row['days']} jours)\n")
                    f.write(f"  Ticker: {row['ticker']}\n")
                    f.write(f"  Buy & Hold: {row['bh_return']:+.2f}% (DD: {row['bh_max_dd']:.2f}%)\n")
                    f.write(f"  Adaptative: {row['adaptive_return']:+.2f}% (DD: {row['adaptive_max_dd']:.2f}%)\n")
                    f.write(f"  Trades: {row['adaptive_trades']} (Win Rate: {row['adaptive_win_rate']:.1f}%)\n")
                    f.write(f"  Protection: {row['protection']:+.2f}% de drawdown evite\n")
                    f.write(f"  Outperformance: {row['outperformance']:+.2f}%\n")
                
                f.write(f"\n{'='*80}\n")
                f.write("STATISTIQUES GLOBALES:\n")
                f.write(f"{'='*80}\n")
                f.write(f"Rendement moyen Buy & Hold:     {df['bh_return'].mean():+.2f}%\n")
                f.write(f"Rendement moyen Adaptative:     {df['adaptive_return'].mean():+.2f}%\n")
                f.write(f"Protection moyenne:             {df['protection'].mean():+.2f}%\n")
                f.write(f"Outperformance moyenne:         {df['outperformance'].mean():+.2f}%\n")
                
                wins = sum(1 for r in self.results if r['outperformance'] > 0)
                f.write(f"\nScenarios gagnants: {wins}/{len(self.results)}\n")
            
            print(f"\n[SAVE] Rapport sauvegarde: {filename}")
            
        except Exception as e:
            print(f"\n[WARNING] Erreur lors de la sauvegarde: {str(e)}")


def main():
    """Point d'entree principal"""
    print("\n" + "=" * 80)
    print("[ROCKET] LANCEMENT DES TESTS BEAR MARKET - ETAPE 8")
    print("=" * 80)
    
    tester = BearMarketTester()
    tester.run_all_tests()
    
    print("\n" + "=" * 80)
    print("[OK] TESTS TERMINES")
    print("=" * 80)


if __name__ == "__main__":
    main()
