"""
Module de backtesting - simule l'execution des trades
"""
import numpy as np
import pandas as pd


class BacktestEngine:
    """Simule l'exécution des trades et calcule les performances"""
    
    # Seuils de volatilité annualisée pour le sizing dynamique
    VOL_LOW = 0.15   # < 15% → plein sizing
    VOL_HIGH = 0.35  # > 35% → sizing minimal

    def __init__(self, initial_capital=10000, position_size_pct=0.95,
                 stop_loss_pct=-2.0, take_profit_pct=5.0, use_trend_filter=True,
                 commission_pct=0.1, volatility_scaling=True, min_position_pct=0.40,
                 slippage_pct=0.05, circuit_breaker_vol=0.80, max_trades=None):
        """
        Args:
            initial_capital: Capital initial en $
            position_size_pct: % du capital à utiliser par trade (max)
            stop_loss_pct: Stop loss en % (ex: -2 pour -2%)
            take_profit_pct: Take profit en % (ex: 5 pour +5%)
            use_trend_filter: Utiliser SMA 200 comme trend filter
            commission_pct: Commission par trade en % de la valeur (défaut 0.1%)
            volatility_scaling: Réduire la taille de position en haute volatilité
            min_position_pct: Taille de position minimale (quand vol très haute)
            slippage_pct: Slippage modélisé en % du prix (défaut 0.05% = 0.5bp)
            circuit_breaker_vol: Bloquer les achats si vol annualisée >= seuil (défaut 80%)
        """
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.stop_loss_pct = stop_loss_pct / 100.0  # Convertir en decimal
        self.take_profit_pct = take_profit_pct / 100.0
        self.use_trend_filter = use_trend_filter
        self.commission_pct = commission_pct / 100.0  # Convertir en decimal
        self.volatility_scaling = volatility_scaling
        self.min_position_pct = min_position_pct
        self.slippage_pct = slippage_pct / 100.0       # Convertir en decimal
        self.circuit_breaker_vol = circuit_breaker_vol  # Seuil vol annualisée (80%)
        self.max_trades = max_trades  # Nombre max de trades acheteurs (None = illimité)
        self._executed_buys = 0
        self.trades = []
        self.portfolio_value = [initial_capital]
        self.cash = initial_capital
        self.position = 0  # Nombre d'actions possédées
        self.entry_price = None
        self.total_commissions = 0.0
        self.total_slippage = 0.0
        self._current_vol = 0.0  # Volatilité courante (mise à jour dans run_backtest)
    
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

        # Pré-calculer la volatilité roulante 20j annualisée (pour le sizing dynamique)
        if self.volatility_scaling and 'Close' in data.columns:
            _vol_series = data['Close'].pct_change().rolling(20).std() * np.sqrt(252)
        else:
            _vol_series = None

        # Compteurs de diagnostic
        n_buy_signals = 0
        n_blocked_by_filter = 0
        n_no_position = 0
        n_blocked_by_circuit_breaker = 0

        for idx, (date, pred) in enumerate(zip(test_dates, predictions)):
            if date not in data.index:
                continue
            
            price = data.loc[date, 'Close']
            # Convertir en scalaire si c'est une Series
            if isinstance(price, pd.Series):
                price = price.values[0]
            price = float(price)
            
            signal = int(pred)  # 1 = BUY, 0 = SELL

            # Mettre à jour la volatilité courante (pour sizing dynamique)
            if _vol_series is not None and date in _vol_series.index:
                vol = _vol_series.loc[date]
                if isinstance(vol, pd.Series):
                    vol = vol.values[0]
                if not pd.isna(vol):
                    self._current_vol = float(vol)

            # Vérifier trend filter - filtre souple : bloquer seulement si fort bear (-15% sous SMA_200)
            trend_ok = True
            if self.use_trend_filter and 'SMA_200' in data.columns:
                if signal == 1:
                    sma_200 = data.loc[date, 'SMA_200']
                    if isinstance(sma_200, pd.Series):
                        sma_200 = sma_200.values[0]
                    if not pd.isna(sma_200):
                        sma_200 = float(sma_200)
                        # Bloquer uniquement si prix > 20% sous SMA_200 (crash sevère confirmé)
                        price_vs_sma200 = (price - sma_200) / sma_200
                        trend_ok = price_vs_sma200 > -0.20
            
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
            
            # Circuit breaker: bloquer les achats si volatilité extrême
            if signal == 1 and self._current_vol >= self.circuit_breaker_vol:
                n_blocked_by_circuit_breaker += 1
                signal = 0  # Force HOLD — volatilité extrême

            # BUY signal
            if signal == 1:
                n_buy_signals += 1
                if self.position == 0 and trend_ok:
                    if self.max_trades is None or self._executed_buys < self.max_trades:
                        self._execute_buy(date, price, reason="Buy Signal")
                        self._executed_buys += 1
                    # else: cap atteint, on ne prend plus de nouvelles positions
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
              f"Bloques (circuit breaker vol): {n_blocked_by_circuit_breaker} | "
              f"Deja en position: {n_no_position} | "
              f"Executes: {len([t for t in self.trades if t['type'] == 'BUY'])}")

        return self._generate_report(data.index[0], data.index[-1])
    
    def _get_effective_position_pct(self):
        """
        Calcule la taille de position effective selon la volatilité courante.
        Interpolation linéaire entre max et min selon la vol annualisée.
        """
        if not self.volatility_scaling or self._current_vol == 0.0:
            return self.position_size_pct

        vol = self._current_vol
        if vol <= self.VOL_LOW:
            return self.position_size_pct
        elif vol >= self.VOL_HIGH:
            return self.min_position_pct
        else:
            # Interpolation linéaire entre plein sizing et sizing minimum
            t = (vol - self.VOL_LOW) / (self.VOL_HIGH - self.VOL_LOW)
            return self.position_size_pct - t * (self.position_size_pct - self.min_position_pct)

    def _execute_buy(self, date, price, reason="Buy Signal"):
        """Exécute un achat avec frais de commission, slippage et sizing dynamique"""
        # Slippage: prix effectif majoré à l'achat (market impact)
        effective_price = price * (1.0 + self.slippage_pct)
        slippage_cost = (effective_price - price)

        effective_pct = self._get_effective_position_pct()
        gross_cost = self.cash * effective_pct
        commission = gross_cost * self.commission_pct
        net_cost = gross_cost - commission
        position_size = net_cost / effective_price
        self.position += position_size
        self.cash -= gross_cost  # Déduit la totalité (frais inclus)
        self.entry_price = effective_price
        self.total_commissions += commission
        self.total_slippage += slippage_cost * position_size

        self.trades.append({
            'date': date,
            'type': 'BUY',
            'price': price,
            'effective_price': effective_price,
            'quantity': position_size,
            'cost': net_cost,
            'commission': commission,
            'position_pct_used': round(effective_pct * 100, 1),
            'vol_at_entry': round(self._current_vol * 100, 1),
            'reason': reason
        })
    
    def _execute_sell(self, date, price, reason="Sell Signal"):
        """Exécute une vente avec frais de commission et slippage"""
        if self.position > 0:
            # Slippage: prix effectif minoré à la vente (market impact)
            effective_price = price * (1.0 - self.slippage_pct)
            slippage_cost = (price - effective_price)
            self.total_slippage += slippage_cost * self.position

            gross_proceeds = self.position * effective_price
            commission = gross_proceeds * self.commission_pct
            net_proceeds = gross_proceeds - commission
            # Le profit tient compte des frais d'achat ET de vente
            profit = net_proceeds - (self.entry_price * self.position)
            self.cash += net_proceeds
            self.total_commissions += commission

            self.trades.append({
                'date': date,
                'type': 'SELL',
                'price': price,
                'effective_price': effective_price,
                'quantity': self.position,
                'proceeds': net_proceeds,
                'commission': commission,
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
        
        # Win rate et statistiques de trades
        if sell_trades > 0:
            profitable_trades = len([t for t in self.trades if t['type'] == 'SELL' and t['profit'] > 0])
            win_rate = (profitable_trades / sell_trades) * 100
            all_pnls = [t['profit'] for t in self.trades if t['type'] == 'SELL']
            loss_pnls = [t['profit'] for t in self.trades if t['type'] == 'SELL' and t['profit'] < 0]
            avg_profit = float(np.mean(all_pnls)) if all_pnls else 0.0
            # np.mean([]) retourne NaN — utiliser la liste filtrée pour éviter ce bug silencieux
            avg_loss = float(np.mean(loss_pnls)) if loss_pnls else 0.0
        else:
            win_rate = 0
            avg_profit = 0.0
            avg_loss = 0.0
        
        # Maximum Drawdown
        portfolio_array = np.array(self.portfolio_value)
        running_max = np.maximum.accumulate(portfolio_array)
        drawdown = (portfolio_array - running_max) / running_max
        max_drawdown = np.min(drawdown) * 100
        
        # Sharpe ratio (annualisé, base daily returns)
        pv_array = np.array(self.portfolio_value)
        daily_returns = np.diff(pv_array) / pv_array[:-1]
        sharpe = (np.mean(daily_returns) / (np.std(daily_returns) + 1e-9)) * np.sqrt(252) if len(daily_returns) > 1 else 0.0

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
            'sharpe_ratio': round(sharpe, 3),
            'total_commissions': round(self.total_commissions, 2),
            'commission_pct_used': self.commission_pct * 100,
            'total_slippage': round(self.total_slippage, 2),
            'slippage_pct_used': self.slippage_pct * 100,
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
        print(f"Sharpe Ratio (annualisé): {report['sharpe_ratio']:.3f}")
        print(f"Frais totaux: ${report['total_commissions']:.2f} ({report['commission_pct_used']:.2f}%/trade)")
        print(f"Slippage total: ${report['total_slippage']:.2f} ({report['slippage_pct_used']:.3f}%/trade)")
        print("="*70)
        
        if len(report['trades_df']) > 0:
            print("\n[LIST] Derniers trades:")
            print(report['trades_df'].tail(10).to_string())


if __name__ == "__main__":
    # Test
    pass
