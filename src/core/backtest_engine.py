"""
Module de backtesting - simule l'execution des trades
"""
import numpy as np
import pandas as pd


class BacktestEngine:
    """Simule l'exécution des trades et calcule les performances"""
    
    def __init__(self, initial_capital=10000, position_size_pct=0.95, 
                 stop_loss_pct=-2.0, take_profit_pct=5.0, use_trend_filter=True):
        """
        Args:
            initial_capital: Capital initial en $
            position_size_pct: % du capital à utiliser par trade
            stop_loss_pct: Stop loss en % (ex: -2 pour -2%)
            take_profit_pct: Take profit en % (ex: 5 pour +5%)
            use_trend_filter: Utiliser SMA 200 comme trend filter
        """
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.stop_loss_pct = stop_loss_pct / 100.0  # Convertir en decimal
        self.take_profit_pct = take_profit_pct / 100.0
        self.use_trend_filter = use_trend_filter
        self.trades = []
        self.portfolio_value = [initial_capital]
        self.cash = initial_capital
        self.position = 0  # Nombre d'actions possédées
        self.entry_price = None
    
    def run_backtest(self, data, model, X_test, test_dates, predictions):
        """
        Lance le backtest
        
        Args:
            data: DataFrame complet avec OHLCV
            model: Modèle entraîné
            X_test: Features de test
            test_dates: Index des dates de test
            predictions: Prédictions du modèle
        
        Returns:
            Résultats du backtest
        """
        print("\n[CHART] Lancement du backtest...")

        # Compteurs de diagnostic
        n_buy_signals = 0
        n_blocked_by_filter = 0
        n_no_position = 0

        for idx, (date, pred) in enumerate(zip(test_dates, predictions)):
            if date not in data.index:
                continue
            
            price = data.loc[date, 'Close']
            # Convertir en scalaire si c'est une Series
            if isinstance(price, pd.Series):
                price = price.values[0]
            price = float(price)
            
            signal = int(pred)  # 1 = BUY, 0 = SELL
            
            # Vérifier trend filter - filtre souple : bloquer seulement si fort bear (-15% sous SMA_200)
            trend_ok = True
            if self.use_trend_filter and 'SMA_200' in data.columns:
                if signal == 1:
                    sma_200 = data.loc[date, 'SMA_200']
                    if isinstance(sma_200, pd.Series):
                        sma_200 = sma_200.values[0]
                    if not pd.isna(sma_200):
                        sma_200 = float(sma_200)
                        # Bloquer uniquement si prix > 15% sous SMA_200 (tendance baissière sévère)
                        price_vs_sma200 = (price - sma_200) / sma_200
                        trend_ok = price_vs_sma200 > -0.15
            
            # Vérifier Stop Loss et Take Profit si on a une position ouverte
            if self.position > 0:
                pnl_pct = (price - self.entry_price) / self.entry_price
                
                # Take Profit atteint
                if pnl_pct >= self.take_profit_pct:
                    self._execute_sell(date, price, reason="Take Profit")
                # Stop Loss atteint
                elif pnl_pct <= self.stop_loss_pct:
                    self._execute_sell(date, price, reason="Stop Loss")
                # SELL signal
                elif signal == 0:
                    self._execute_sell(date, price, reason="Sell Signal")
            
            # BUY signal
            if signal == 1:
                n_buy_signals += 1
                if self.position == 0 and trend_ok:
                    self._execute_buy(date, price, reason="Buy Signal")
                elif not trend_ok:
                    n_blocked_by_filter += 1
                elif self.position > 0:
                    n_no_position += 1
            
            # Update portfolio value
            if self.position > 0:
                current_value = self.cash + (self.position * price)
            else:
                current_value = self.cash
            
            self.portfolio_value.append(current_value)
        
        # Fermer toute position ouverte
        if self.position > 0:
            last_price = data.iloc[-1]['Close']
            self._execute_sell(data.index[-1], last_price, reason="Position Close")

        # Diagnostic
        print(f"[DEBUG] Signaux BUY generés: {n_buy_signals} | "
              f"Bloques (trend filter): {n_blocked_by_filter} | "
              f"Deja en position: {n_no_position} | "
              f"Executes: {len([t for t in self.trades if t['type'] == 'BUY'])}")

        return self._generate_report(data.index[0], data.index[-1])
    
    def _execute_buy(self, date, price, reason="Buy Signal"):
        """Exécute un achat"""
        position_size = (self.cash * self.position_size_pct) / price
        self.position += position_size
        self.cash -= position_size * price
        self.entry_price = price
        
        self.trades.append({
            'date': date,
            'type': 'BUY',
            'price': price,
            'quantity': position_size,
            'cost': position_size * price,
            'reason': reason
        })
    
    def _execute_sell(self, date, price, reason="Sell Signal"):
        """Exécute une vente"""
        if self.position > 0:
            profit = (price - self.entry_price) * self.position
            self.cash += self.position * price
            
            self.trades.append({
                'date': date,
                'type': 'SELL',
                'price': price,
                'quantity': self.position,
                'proceeds': self.position * price,
                'profit': profit,
                'profit_pct': (profit / (self.entry_price * self.position)) * 100,
                'reason': reason
            })
            
            self.position = 0
            self.entry_price = None
    
    def _generate_report(self, start_date, end_date):
        """Génère un rapport des performances"""
        trades_df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        
        # Calculer les métriques
        total_return_pct = ((self.portfolio_value[-1] - self.initial_capital) / self.initial_capital) * 100
        
        buy_trades = len([t for t in self.trades if t['type'] == 'BUY'])
        sell_trades = len([t for t in self.trades if t['type'] == 'SELL'])
        
        # Win rate
        if sell_trades > 0:
            profitable_trades = len([t for t in self.trades if t['type'] == 'SELL' and t['profit'] > 0])
            win_rate = (profitable_trades / sell_trades) * 100
            avg_profit = np.mean([t['profit'] for t in self.trades if t['type'] == 'SELL'])
            avg_loss = np.mean([t['profit'] for t in self.trades if t['type'] == 'SELL' and t['profit'] < 0])
        else:
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
        
        # Maximum Drawdown
        portfolio_array = np.array(self.portfolio_value)
        running_max = np.maximum.accumulate(portfolio_array)
        drawdown = (portfolio_array - running_max) / running_max
        max_drawdown = np.min(drawdown) * 100
        
        report = {
            'start_date': start_date,
            'end_date': end_date,
            'initial_capital': self.initial_capital,
            'final_value': self.portfolio_value[-1],
            'total_return_pct': total_return_pct,
            'total_trades': len(self.trades),
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'trades_df': trades_df
        }
        
        return report
    
    def print_report(self, report):
        """Affiche le rapport formate"""
        print("\n" + "="*70)
        print("[CHART] RAPPORT DE BACKTEST")
        print("="*70)
        print(f"Période: {report['start_date']} -> {report['end_date']}")
        print(f"Capital initial: ${report['initial_capital']:.2f}")
        print(f"Valeur finale: ${report['final_value']:.2f}")
        print(f"Rendement total: {report['total_return_pct']:.2f}%")
        print("-"*70)
        print(f"Nombre total de trades: {report['total_trades']}")
        print(f"  - Achats: {report['buy_trades']}")
        print(f"  - Ventes: {report['sell_trades']}")
        print(f"Taux de réussite: {report['win_rate']:.2f}%")
        print(f"Profit moyen par trade: ${report['avg_profit']:.2f}")
        print(f"Perte moyenne par trade: ${report['avg_loss']:.2f}")
        print(f"Perte maximale (Drawdown): {report['max_drawdown']:.2f}%")
        print("="*70)
        
        if len(report['trades_df']) > 0:
            print("\n[LIST] Derniers trades:")
            print(report['trades_df'].tail(10).to_string())


if __name__ == "__main__":
    # Test
    pass
