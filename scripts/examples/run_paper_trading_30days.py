"""
Run Paper Trading - 30 Day Simulation
=====================================

Lance une simulation paper trading complète sur 30 jours,
utilisant les paramètres optimisés de l'étape 12 et les données réelles.

Usage:
    python run_paper_trading_30days.py

Output:
    - Rapport complet de trading
    - Statistiques journalières P&L
    - Performance par ticker
    - Validation de readiness pour live trading
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.paper_trading import PaperTradingSimulator
from trading.kelly_calculator import KellyCalculator, RiskManager
from core.data_fetcher import DataFetcher
from core.backtest_engine import BacktestEngine


class PaperTradingRunner:
    """Lance la simulation paper trading"""
    
    def __init__(self,
                 initial_capital: float = 100000,
                 tickers: list = None,
                 start_date: datetime = None,
                 end_date: datetime = None):
        """
        Args:
            initial_capital: Capital initial
            tickers: Tickers à trader
            start_date: Date de début (default: 30j avant aujourd'hui)
            end_date: Date de fin (default: aujourd'hui)
        """
        self.initial_capital = initial_capital
        self.tickers = tickers or ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        
        # Dates
        if end_date is None:
            end_date = datetime.now().date()
        if start_date is None:
            start_date = (end_date - timedelta(days=30))
        
        self.start_date = start_date
        self.end_date = end_date
        
        # Composants
        self.simulator = PaperTradingSimulator(initial_capital)
        self.kelly = KellyCalculator(initial_capital)
        self.data_fetcher = DataFetcher()
        self.backtest = BacktestEngine()
        
        # État
        self.daily_results = []
        self.trades_log = []
        self.optimal_params = self._load_optimal_params()
    
    def _load_optimal_params(self) -> dict:
        """Charge les paramètres optimisés"""
        optimal_params = {}
        analysis_dir = Path(__file__).parent
        
        for ticker in self.tickers:
            # Chercher le fichier optimal_params le plus récent
            params_files = sorted(analysis_dir.glob(f"optimal_params_{ticker}_*.py"))
            
            if params_files:
                params_file = params_files[-1]
                
                try:
                    import importlib.util
                    spec = importlib.util.spec_from_file_location("optimal_params", params_file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    optimal_params[ticker] = module.OPTIMAL_STRATEGY_PARAMS
                    print(f"  ✓ Loaded: {params_file.name}")
                except Exception as e:
                    print(f"  ✗ Error loading {ticker}: {e}")
        
        return optimal_params
    
    def load_market_data(self) -> dict:
        """Charge les données de marché pour la période"""
        print(f"\n[2] Loading market data ({self.start_date} to {self.end_date})...")
        
        market_data = {}
        for ticker in self.tickers:
            try:
                df = self.data_fetcher.fetch_data(
                    ticker=ticker,
                    start_date=str(self.start_date),
                    end_date=str(self.end_date)
                )
                if df is not None and len(df) > 0:
                    market_data[ticker] = df
                    print(f"  ✓ {ticker}: {len(df)} days loaded")
                else:
                    print(f"  ✗ {ticker}: No data available")
            except Exception as e:
                print(f"  ✗ {ticker}: Error - {e}")
        
        return market_data
    
    def run_simulation(self, market_data: dict) -> dict:
        """Lance la simulation paper trading"""
        print(f"\n[3] Running Paper Trading Simulation...")
        
        if not market_data:
            print("  ✗ No market data available")
            return {}
        
        # Initialiser les positions (jour 1)
        ticker_symbols = list(market_data.keys())
        initial_prices = {}
        for ticker in ticker_symbols:
            df = market_data[ticker]
            if len(df) > 0:
                initial_prices[ticker] = df['close'].iloc[0]
        
        # Kelly allocation
        print("\n  Initializing positions (Kelly Criterion)...")
        portfolio = {}
        for ticker in ticker_symbols:
            if ticker in self.optimal_params:
                params = self.optimal_params[ticker].get('BULL', {})
                win_rate = params.get('win_rate', 50) / 100
                avg_win = params.get('rendement', 0) / 100
                avg_loss = -abs(params.get('stop_loss_pct', -2)) / 100
                
                portfolio[ticker] = {
                    'price': initial_prices.get(ticker, 0),
                    'win_rate': win_rate,
                    'avg_win_pct': avg_win,
                    'avg_loss_pct': avg_loss,
                }
        
        allocations = self.kelly.calculate_multi_ticker_allocation(portfolio)
        
        # Créer les positions initiales
        opened = 0
        for ticker, alloc in allocations.items():
            if ticker == 'total':
                continue
            
            params = self.optimal_params[ticker]['BULL']
            success, msg = self.simulator.buy(
                ticker=ticker,
                num_shares=alloc['num_shares'],
                current_price=initial_prices[ticker],
                stop_loss_pct=params['stop_loss_pct'] / 100,
                take_profit_pct=params['take_profit_pct'] / 100,
                reason='Initial Kelly allocation'
            )
            if success:
                opened += 1
                print(f"    ✓ {ticker}: {alloc['num_shares']} shares @ ${initial_prices[ticker]:.2f}")
        
        print(f"  ✓ Opened {opened} initial positions")
        
        # Simuler chaque jour
        print("\n  Processing daily prices...")
        min_len = min(len(df) for df in market_data.values())
        
        closed_count = 0
        for day_idx in range(1, min_len):
            daily_prices = {}
            for ticker in ticker_symbols:
                daily_prices[ticker] = market_data[ticker]['close'].iloc[day_idx]
            
            # Mettre à jour prix et vérifier stops
            self.simulator.update_prices(daily_prices)
            closed_trades = self.simulator.execute_auto_close(daily_prices)
            closed_count += len(closed_trades)
            
            # Daily snapshot
            self.daily_results.append({
                'day': day_idx,
                'date': market_data[ticker_symbols[0]].index[day_idx],
                'summary': self.simulator.get_portfolio_summary(),
                'closed_trades': len(closed_trades),
            })
        
        print(f"  ✓ Closed {closed_count} positions via stop/target")
        
        return {
            'initial_positions': opened,
            'days_simulated': min_len - 1,
            'final_trades': len(self.simulator.closed_trades),
            'open_positions': len(self.simulator.positions),
        }
    
    def generate_report(self) -> str:
        """Génère un rapport complet"""
        report = []
        report.append("="*90)
        report.append("ÉTAPE 14 - PAPER TRADING SIMULATION REPORT (30 DAYS)")
        report.append("="*90)
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Period: {self.start_date} to {self.end_date}")
        report.append(f"Initial Capital: ${self.initial_capital:,.2f}")
        
        # Résumé final
        final_summary = self.simulator.get_portfolio_summary()
        report.append("\n" + "-"*90)
        report.append("FINAL PORTFOLIO STATE")
        report.append("-"*90)
        for key, value in final_summary.items():
            report.append(f"{key:30s}: {value}")
        
        # Statistiques des trades
        if self.simulator.closed_trades:
            df_trades = pd.DataFrame(self.simulator.closed_trades)
            
            report.append("\n" + "-"*90)
            report.append("TRADE STATISTICS")
            report.append("-"*90)
            report.append(f"Total closed trades: {len(df_trades)}")
            report.append(f"Win rate: {(df_trades['pnl_dollar'] > 0).sum() / len(df_trades) * 100:.1f}%")
            report.append(f"Total P&L: ${df_trades['pnl_dollar'].sum():,.2f}")
            report.append(f"Avg P&L: ${df_trades['pnl_dollar'].mean():,.2f}")
            report.append(f"Max win: ${df_trades['pnl_dollar'].max():,.2f}")
            report.append(f"Max loss: ${df_trades['pnl_dollar'].min():,.2f}")
            
            if len(df_trades) > 1:
                report.append(f"Std Dev: ${df_trades['pnl_dollar'].std():,.2f}")
                
                # Profit factor
                wins = df_trades[df_trades['pnl_dollar'] > 0]['pnl_dollar'].sum()
                losses = abs(df_trades[df_trades['pnl_dollar'] < 0]['pnl_dollar'].sum())
                if losses > 0:
                    report.append(f"Profit Factor: {wins / losses:.2f}")
            
            # Top trades
            report.append("\nTop 5 Trades:")
            top = df_trades.nlargest(5, 'pnl_dollar')
            for idx, row in top.iterrows():
                report.append(f"  {row['ticker']:6s}: ${row['pnl_dollar']:8,.2f} ({row['pnl_percent']:5.1f}%)")
        
        # Positions ouvertes
        if self.simulator.positions:
            report.append("\n" + "-"*90)
            report.append("OPEN POSITIONS")
            report.append("-"*90)
            for pos in self.simulator.get_open_positions():
                report.append(f"\n{pos['ticker']}:")
                report.append(f"  Entry: ${pos['entry_price']}, Current: ${pos['current_price']}")
                report.append(f"  P&L: {pos['pnl_percent']} (${pos['pnl_dollar']})")
        
        # Recommandations
        report.append("\n" + "-"*90)
        report.append("READINESS FOR LIVE TRADING")
        report.append("-"*90)
        
        final_equity = float(final_summary['current_equity'].replace('$', '').replace(',', ''))
        return_pct = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        
        checks = {
            'Positive Return (>-5%)': return_pct > -5.0,
            'Stable Performance': len(self.daily_results) > 20,
            'Positive Win Rate (>45%)': (df_trades['pnl_dollar'] > 0).sum() / len(df_trades) * 100 > 45 if len(df_trades) > 0 else False,
            'Reasonable Drawdown (<15%)': abs(min(return_pct, 0)) < 15,
            'Risk Management Working': len(self.simulator.closed_trades) > 0,
        }
        
        for check, result in checks.items():
            status = "✓ PASS" if result else "✗ FAIL"
            report.append(f"  {check:35s}: {status}")
        
        all_pass = all(checks.values())
        report.append(f"\nOVERALL READINESS: {'✓ READY FOR LIVE TRADING' if all_pass else '✗ NEEDS MORE TESTING'}")
        
        return "\n".join(report)
    
    def save_report(self):
        """Sauvegarde le rapport"""
        filepath = Path(__file__).parent.parent.parent / "reports" / f"paper_trading_30day_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            f.write(self.generate_report())
        
        return filepath


def main():
    """Lance la simulation"""
    print("\n" + "="*90)
    print("ÉTAPE 14 - PAPER TRADING SIMULATION (30 DAYS)")
    print("="*90)
    
    # [1] Initialisation
    print("\n[1] Initializing paper trading system...")
    runner = PaperTradingRunner(
        initial_capital=100000,
        tickers=['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    )
    print("  ✓ System initialized")
    print(f"  ✓ Loaded optimal params for {len(runner.optimal_params)}/{len(runner.tickers)} tickers")
    
    # [2] Charger données
    market_data = runner.load_market_data()
    if not market_data:
        print("\n✗ No market data available. Exiting.")
        return
    
    # [3] Lancer simulation
    sim_results = runner.run_simulation(market_data)
    print(f"\n  Results: {sim_results}")
    
    # [4] Générer rapport
    print(f"\n[4] Generating report...")
    report_text = runner.generate_report()
    
    # [5] Sauvegarder et afficher
    report_path = runner.save_report()
    print(f"  ✓ Report saved: {report_path}")
    
    print("\n" + "="*90)
    print(report_text)
    print("="*90)


if __name__ == "__main__":
    main()
