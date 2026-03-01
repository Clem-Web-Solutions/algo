"""
Test sur Bear Markets - Étape 7.1
Teste le système de trading sur des périodes de baisse de marché
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

from data_fetcher import DataFetcher
from feature_engineering import FeatureEngineering
from trading_model import TradingModel
from backtest_engine import BacktestEngine
from market_regime_detector import MarketRegimeDetector
from adaptive_strategy import AdaptiveStrategy


class BearMarketTester:
    """Teste les performances sur les bear markets historiques"""
    
    # Périodes de bear market reconnues
    BEAR_MARKET_PERIODS = {
        '2008_CRASH': {
            'start': '2008-09-01',
            'end': '2009-03-31',
            'description': '2008: Crise financière mondiale'
        },
        '2020_COVID': {
            'start': '2020-01-01',
            'end': '2020-06-30',
            'description': '2020: Crash COVID et récupération'
        },
        '2022_DECLINE': {
            'start': '2022-01-01',
            'end': '2022-09-30',
            'description': '2022: Remontée des taux FED'
        }
    }
    
    def __init__(self, ticker='SPY', data_dir='data'):
        self.ticker = ticker
        self.data_dir = data_dir
        self.fetcher = DataFetcher(data_dir=data_dir)
        self.results = {}
    
    def run_all_periods(self):
        """Teste sur toutes les périodes de bear market"""
        print("\n" + "="*80)
        print(f"🔴 TEST SUR BEAR MARKETS - {self.ticker}")
        print("="*80)
        
        for period_name, period_info in self.BEAR_MARKET_PERIODS.items():
            print(f"\n{'='*80}")
            print(f"Period: {period_name}")
            print(f"Description: {period_info['description']}")
            print(f"Dates: {period_info['start']} à {period_info['end']}")
            print('='*80)
            
            try:
                result = self.test_period(
                    period_name,
                    period_info['start'],
                    period_info['end']
                )
                self.results[period_name] = result
                
                print(f"\n✅ {period_name} complété")
                
            except Exception as e:
                print(f"\n❌ {period_name} échoué: {str(e)}")
                self.results[period_name] = {'error': str(e)}
        
        self.generate_summary()
    
    def test_period(self, period_name, start_date, end_date):
        """Test une période spécifique"""
        
        # 1. Récupérer les données
        print(f"\n[1/5] Téléchargement des données {self.ticker}...")
        try:
            data = self.fetcher.fetch_stock_data(self.ticker, start_date, end_date)
        except:
            # Si le téléchargement échoue, essayer avec des données locales
            print(f"⚠️ Utilisation de données locales si disponibles...")
            data = self._try_load_local_data(self.ticker, start_date, end_date)
            if data is None:
                raise Exception("Impossible de charger les données")
        
        if len(data) < 50:
            raise Exception(f"Insuffisamment de données: {len(data)} jours")
        
        # 2. Créer les features
        print(f"[2/5] Création des features...")
        fe = FeatureEngineering()
        data = fe.add_technical_indicators(data)
        
        # 3. Détecter les régimes
        print(f"[3/5] Détection des régimes de marché...")
        regime_history = MarketRegimeDetector.get_regime_history(data)
        regime_stats = MarketRegimeDetector.get_regime_statistics(data, periods=len(data))
        
        # 4. Entraîner le modèle
        print(f"[4/5] Entraînement du modèle...")
        model = TradingModel(model_type='neural_network')
        X, y, test_dates, test_indices = model.prepare_data(data, test_size=0.3)
        
        if len(test_indices) == 0:
            raise Exception("Pas assez de données pour le test")
        
        model.train(X, y)
        
        # 5. Backtester avec stratégie adaptative
        print(f"[5/5] Backtesting avec stratégie adaptative...")
        
        # Backtester classique
        engine_standard = BacktestEngine()
        results_standard = engine_standard.run_backtest(
            data, model, X, test_dates, 
            model.model.predict(X[test_indices]) if test_indices is not None else []
        )
        
        # Backtester avec régimes adaptatifs
        engine_adaptive = BacktestEngine()
        results_adaptive = self._run_adaptive_backtest(
            data, model, X, test_dates, test_indices, 
            engine_adaptive, regime_history
        )
        
        # Calculer les statistiques
        buy_hold_return = self._calculate_buy_hold_return(data)
        
        return {
            'period_name': period_name,
            'start_date': start_date,
            'end_date': end_date,
            'data_length': len(data),
            'standard_backtest': results_standard,
            'adaptive_backtest': results_adaptive,
            'buy_hold_return': buy_hold_return,
            'regime_stats': regime_stats,
            'regime_history': regime_history
        }
    
    def _try_load_local_data(self, ticker, start_date, end_date):
        """Essaie de charger les données locales"""
        for file in os.listdir(self.data_dir):
            if ticker in file:
                try:
                    data = pd.read_csv(os.path.join(self.data_dir, file), index_col=0, parse_dates=True)
                    data_start = pd.to_datetime(start_date)
                    data_end = pd.to_datetime(end_date)
                    return data[(data.index >= data_start) & (data.index <= data_end)]
                except:
                    continue
        return None
    
    def _run_adaptive_backtest(self, data, model, X, test_dates, test_indices, 
                               engine, regime_history):
        """Exécute un backtest adaptatif basé sur les régimes"""
        
        trades_adaptive = []
        portfolio_adaptive = [engine.initial_capital]
        cash_adaptive = engine.initial_capital
        position_adaptive = 0
        entry_price_adaptive = None
        current_regime = 'UNKNOWN'
        current_confidence = 0.5
        
        predictions = model.model.predict(X[test_indices]) if test_indices is not None else []
        
        for idx, (date, pred) in enumerate(zip(test_dates, predictions)):
            if date not in data.index:
                continue
            
            price = float(data.loc[date, 'Close'])
            
            # Détecter le régime pour cette date
            subset_data = data.iloc[:data.index.get_loc(date)+1]
            regime_info = MarketRegimeDetector.detect_regime(subset_data)
            current_regime = regime_info['regime']
            current_confidence = regime_info['confidence']
            
            # Adapter la stratégie
            engine_adapted = AdaptiveStrategy.adapt_backtest_engine(
                engine, current_regime, current_confidence
            )
            
            signal = int(pred)  # 1 = BUY, 0 = SELL
            
            # Vérifier trend filter
            trend_ok = True
            if engine_adapted.use_trend_filter and 'SMA_200' in data.columns:
                sma_200 = float(data.loc[date, 'SMA_200'])
                trend_ok = (price > sma_200) if not pd.isna(sma_200) else True
            
            # Gestion des positions
            if position_adaptive > 0:
                pnl_pct = (price - entry_price_adaptive) / entry_price_adaptive
                
                if pnl_pct >= engine_adapted.take_profit_pct:
                    cash_adaptive += position_adaptive * price
                    position_adaptive = 0
                    trades_adaptive.append({
                        'date': date,
                        'action': 'SELL',
                        'reason': 'Take Profit',
                        'price': price,
                        'pnl': (position_adaptive * price) - (position_adaptive * entry_price_adaptive)
                    })
                elif pnl_pct <= engine_adapted.stop_loss_pct:
                    cash_adaptive += position_adaptive * price
                    position_adaptive = 0
                    trades_adaptive.append({
                        'date': date,
                        'action': 'SELL',
                        'reason': 'Stop Loss',
                        'price': price,
                        'pnl': (position_adaptive * price) - (position_adaptive * entry_price_adaptive)
                    })
                elif signal == 0:
                    cash_adaptive += position_adaptive * price
                    position_adaptive = 0
                    trades_adaptive.append({
                        'date': date,
                        'action': 'SELL',
                        'reason': f'Signal ({current_regime})',
                        'price': price
                    })
            
            # BUY signal
            if signal == 1 and position_adaptive == 0 and trend_ok:
                shares = int(cash_adaptive * engine_adapted.position_size_pct / price)
                if shares > 0:
                    entry_price_adaptive = price
                    position_adaptive = shares
                    cash_adaptive -= shares * price
                    trades_adaptive.append({
                        'date': date,
                        'action': 'BUY',
                        'reason': f'Signal ({current_regime})',
                        'price': price,
                        'regime': current_regime
                    })
            
            # Update portfolio
            if position_adaptive > 0:
                current_value = cash_adaptive + (position_adaptive * price)
            else:
                current_value = cash_adaptive
            
            portfolio_adaptive.append(current_value)
        
        # Fermer position finale
        if position_adaptive > 0:
            final_price = float(data.iloc[-1]['Close'])
            cash_adaptive += position_adaptive * final_price
        
        final_value = cash_adaptive
        total_return = ((final_value - engine.initial_capital) / engine.initial_capital * 100)
        
        return {
            'final_value': final_value,
            'total_return': total_return,
            'trades': len(trades_adaptive),
            'portfolio_values': portfolio_adaptive
        }
    
    def _calculate_buy_hold_return(self, data):
        """Calcule le rendement buy & hold"""
        if len(data) < 2:
            return 0.0
        
        first_price = float(data.iloc[0]['Close'])
        last_price = float(data.iloc[-1]['Close'])
        
        return ((last_price - first_price) / first_price * 100)
    
    def generate_summary(self):
        """Génère un résumé des résultats"""
        
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DES TESTS BEAR MARKET")
        print("="*80)
        
        summary_data = []
        
        for period_name, result in self.results.items():
            if 'error' in result:
                print(f"\n❌ {period_name}: {result['error']}")
                continue
            
            standard_return = result['standard_backtest'].get('total_return', 0)
            adaptive_return = result['adaptive_backtest']['total_return']
            buy_hold = result['buy_hold_return']
            regime_stats = result['regime_stats']
            
            print(f"\n📈 {period_name}")
            print(f"   Description: {result.get('description', 'N/A')}")
            print(f"   Durée: {result['data_length']} jours")
            print(f"   Buy & Hold: {buy_hold:+.2f}%")
            print(f"   Stratégie Standard: {standard_return:+.2f}%")
            print(f"   Stratégie Adaptative: {adaptive_return:+.2f}%")
            print(f"   Amélioration: {adaptive_return - standard_return:+.2f}%")
            print(f"   Régimes prédominants: {regime_stats.get('most_common', 'N/A')}")
            
            summary_data.append({
                'Period': period_name,
                'Buy&Hold': buy_hold,
                'Standard': standard_return,
                'Adaptive': adaptive_return,
                'Improvement': adaptive_return - standard_return,
                'Main_Regime': regime_stats.get('most_common', 'N/A')
            })
        
        # Sauvegarder le résumé
        self._save_summary(summary_data)
        
        return summary_data
    
    def _save_summary(self, summary_data):
        """Sauvegarde le résumé en fichier"""
        
        if not summary_data:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reports/bear_market_test_{self.ticker}_{timestamp}.txt"
        
        os.makedirs("reports", exist_ok=True)
        
        with open(filename, 'w') as f:
            f.write("="*80 + "\n")
            f.write("RÉSUMÉ TEST BEAR MARKETS - ÉTAPE 7\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"Ticker: {self.ticker}\n")
            f.write(f"Date de rapport: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("Résultats Globaux:\n")
            f.write("-"*80 + "\n")
            
            for data in summary_data:
                f.write(f"\n{data['Period']}\n")
                f.write(f"  Buy & Hold:   {data['Buy&Hold']:+8.2f}%\n")
                f.write(f"  Standard:     {data['Standard']:+8.2f}%\n")
                f.write(f"  Adaptive:     {data['Adaptive']:+8.2f}%\n")
                f.write(f"  Improvement:  {data['Improvement']:+8.2f}%\n")
                f.write(f"  Main Regime:  {data['Main_Regime']}\n")
            
            # Statistiques globales
            avg_bh = np.mean([d['Buy&Hold'] for d in summary_data])
            avg_standard = np.mean([d['Standard'] for d in summary_data])
            avg_adaptive = np.mean([d['Adaptive'] for d in summary_data])
            
            f.write("\n" + "="*80 + "\n")
            f.write("Moyennes sur les 3 périodes:\n")
            f.write("-"*80 + "\n")
            f.write(f"Buy & Hold (Moyenne):  {avg_bh:+.2f}%\n")
            f.write(f"Standard (Moyenne):    {avg_standard:+.2f}%\n")
            f.write(f"Adaptive (Moyenne):    {avg_adaptive:+.2f}%\n")
            f.write(f"\n✅ Avantage Adaptive vs Standard: {avg_adaptive - avg_standard:+.2f}%\n")
            f.write(f"✅ Avantage Adaptive vs B&H:     {avg_adaptive - avg_bh:+.2f}%\n")


def main():
    """Lance les tests bear market"""
    
    # Tester sur SPY (indice large)
    tester = BearMarketTester(ticker='AAPL')  # Garder AAPL car données dispo
    tester.run_all_periods()
    
    print("\n✅ Tests bear market complétés!")


if __name__ == '__main__':
    main()
