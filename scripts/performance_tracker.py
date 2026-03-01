"""
Performance Tracker - Suivi cumulatif des performances par ticker et par cycle
Persiste l'historique dans un fichier JSON et genere des statistiques de synthese
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional


class PerformanceTracker:
    """Suit et persiste les performances de chaque cycle de training"""

    def __init__(self, history_file):
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(exist_ok=True, parents=True)
        self.data = self._load()

    # ------------------------------------------------------------------
    def _load(self) -> dict:
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return {'tickers': {}, 'global': []}

    def _save(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.data, f, indent=2, default=str)

    # ------------------------------------------------------------------
    def record(self, ticker: str, result: dict):
        """Enregistre un resultat de cycle pour un ticker"""
        if ticker not in self.data['tickers']:
            self.data['tickers'][ticker] = []
        self.data['tickers'][ticker].append(result)

        # Entree globale (tous tickers confondus)
        self.data['global'].append({'ticker': ticker, **result})
        self._save()

    # ------------------------------------------------------------------
    def get_ticker_stats(self, ticker: str, last_n: Optional[int] = None) -> dict:
        """Calcule les statistiques agregees pour un ticker"""
        records = self.data['tickers'].get(ticker, [])
        if last_n:
            records = records[-last_n:]

        if not records:
            return {}

        returns = [r['return_pct'] for r in records]
        win_rates = [r['win_rate'] for r in records]
        drawdowns = [r['max_drawdown'] for r in records]
        n_trades_list = [r['n_trades'] for r in records]

        profitable_cycles = sum(1 for r in returns if r > 0)

        return {
            'ticker': ticker,
            'n_cycles': len(records),
            'total_return_pct': sum(returns),
            'avg_return_pct': sum(returns) / len(returns),
            'best_cycle_pct': max(returns),
            'worst_cycle_pct': min(returns),
            'profitable_cycles': profitable_cycles,
            'profitable_cycles_pct': profitable_cycles / len(records),
            'avg_win_rate': sum(win_rates) / len(win_rates),
            'avg_drawdown': sum(drawdowns) / len(drawdowns),
            'total_trades': sum(n_trades_list),
            'last_return_pct': returns[-1] if returns else 0,
            'last_win_rate': win_rates[-1] if win_rates else 0,
            'trend': self._compute_trend(returns),
        }

    def _compute_trend(self, returns: list) -> str:
        """Retourne IMPROVING / STABLE / DECLINING selon les 3 derniers cycles"""
        if len(returns) < 3:
            return 'INSUFFICIENT_DATA'
        last3 = returns[-3:]
        if last3[-1] > last3[0] + 1.0:
            return 'IMPROVING'
        elif last3[-1] < last3[0] - 1.0:
            return 'DECLINING'
        else:
            return 'STABLE'

    # ------------------------------------------------------------------
    def get_global_stats(self) -> dict:
        """Statistiques globales tous tickers"""
        all_records = self.data['global']
        if not all_records:
            return {}

        returns = [r['return_pct'] for r in all_records]
        return {
            'total_records': len(all_records),
            'avg_return_pct': sum(returns) / len(returns),
            'best_return_pct': max(returns),
            'worst_return_pct': min(returns),
            'profitable_pct': sum(1 for r in returns if r > 0) / len(returns),
        }

    # ------------------------------------------------------------------
    def print_summary(self, logger=None):
        """Affiche un tableau de synthese dans les logs"""
        _log = logger.info if logger else print

        _log("\n" + "=" * 60)
        _log("LEADERBOARD CUMULATIF")
        _log("=" * 60)
        _log(f"{'Ticker':<8} {'Cycles':>6} {'Ret.Total':>10} {'Ret.Moy':>9} "
             f"{'WR.Moy':>8} {'Trades':>7} {'Trend':>12}")
        _log("-" * 60)

        tickers_stats = []
        for ticker in self.data['tickers']:
            stats = self.get_ticker_stats(ticker)
            if stats:
                tickers_stats.append(stats)

        # Trier par rendement total decroissant
        tickers_stats.sort(key=lambda x: x['total_return_pct'], reverse=True)

        for s in tickers_stats:
            _log(
                f"{s['ticker']:<8} "
                f"{s['n_cycles']:>6} "
                f"{s['total_return_pct']:>+9.2f}% "
                f"{s['avg_return_pct']:>+8.2f}% "
                f"{s['avg_win_rate']:>7.1%} "
                f"{s['total_trades']:>7} "
                f"{s['trend']:>12}"
            )

        g = self.get_global_stats()
        if g:
            _log("-" * 60)
            _log(f"  Rendement moyen global: {g['avg_return_pct']:+.2f}% | "
                 f"Profitable: {g['profitable_pct']:.1%} des cycles")
        _log("=" * 60 + "\n")

    # ------------------------------------------------------------------
    def export_csv(self, output_path: Optional[str] = None) -> str:
        """Exporte l'historique complet en CSV"""
        import csv
        path = output_path or str(self.history_file.parent / 'performance_history.csv')
        all_records = self.data['global']
        if not all_records:
            return path

        fieldnames = ['ticker', 'cycle', 'date', 'return_pct', 'win_rate',
                      'n_trades', 'max_drawdown', 'final_value']
        with open(path, 'w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            w.writeheader()
            w.writerows(all_records)
        return path
