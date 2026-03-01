"""
Kelly Criterion & Position Sizing Calculator
=============================================

Calcule la fraction Kelly optimale pour dimensionner les positions
afin de maximiser la croissance à long terme tout en limitant le risque.

Kelly Criterion: f* = (p * b - q) / b
  f* = fraction du capital à risquer
  p = probabilité de gain
  q = probabilité de perte (1-p)
  b = ratio gains/pertes (moyenne gain / moyenne perte)

Formule conservative: f_conservative = f* / 2.5  (limiter surexposure)
"""

import numpy as np
from typing import Dict, Tuple, Optional


class KellyCalculator:
    """Calcule la taille optimale des positions selon Kelly Criterion"""
    
    # Risk limits
    MAX_KELLY_FRACTION = 0.25  # Max 25% du capital par position
    MIN_KELLY_FRACTION = 0.01  # Min 1% pour éviter positions triviales
    KELLY_FRACTION_CONSERVATIVE = 0.5  # Factor de sécurité (0.5 = demi-Kelly)
    
    def __init__(self, 
                 initial_capital: float = 100000.0,
                 max_portfolio_leverage: float = 2.0):
        """
        Args:
            initial_capital: Capital initial en USD
            max_portfolio_leverage: Levier maximum pour le portefeuille (default 2x)
        """
        self.initial_capital = initial_capital
        self.max_portfolio_leverage = max_portfolio_leverage
    
    @staticmethod
    def calculate_kelly_fraction(win_rate: float, 
                                 avg_win_pct: float,
                                 avg_loss_pct: float,
                                 conservative: bool = True) -> float:
        """
        Calcule la fraction de Kelly optimal.
        
        Args:
            win_rate: Taux de gain (0-1, ex: 0.75 = 75%)
            avg_win_pct: Percentile moyen de gain (ex: 0.05 = +5%)
            avg_loss_pct: Percentile moyen de perte (ex: -0.02 = -2%, entrer comme -0.02)
            conservative: Si True, utilise demi-Kelly pour sécurité
            
        Returns:
            Fraction Kelly optimale (ex: 0.25 = 25% du capital à risquer)
        """
        # Paramètres
        p = max(0.01, min(0.99, win_rate))  # Limiter entre 1% et 99%
        q = 1 - p  # Probabilité de perte
        b = -avg_win_pct / avg_loss_pct  # Ratio gains/pertes
        
        # Éviter division par zéro
        if avg_loss_pct == 0 or b <= 0:
            return 0.01
        
        # Formule Kelly
        f_star = (p * b - q) / b
        
        # Appliquer factor conservatif si demandé
        if conservative:
            f_star = f_star * KellyCalculator.KELLY_FRACTION_CONSERVATIVE
        
        # Limiter entre min et max
        f_star = max(KellyCalculator.MIN_KELLY_FRACTION, 
                     min(KellyCalculator.MAX_KELLY_FRACTION, f_star))
        
        return f_star
    
    def calculate_position_size(self, 
                               ticker: str,
                               win_rate: float,
                               avg_win_pct: float,
                               avg_loss_pct: float,
                               current_stock_price: float,
                               conservative: bool = True) -> Tuple[int, float, float]:
        """
        Calcule la taille d'une position (nombre d'actions).
        
        Args:
            ticker: Symbole du ticker (ex: "AAPL")
            win_rate: Taux de gain empirique (0-1)
            avg_win_pct: Rendement moyen par trade gagnant
            avg_loss_pct: Perte moyenne par trade perdant (négatif)
            current_stock_price: Prix actuel de l'action
            conservative: Si True, divise Kelly par 2.5 pour sécurité
            
        Returns:
            (num_shares, capital_allocated, kelly_fraction)
        """
        # 1. Calculer fraction Kelly
        kelly_f = self.calculate_kelly_fraction(
            win_rate, avg_win_pct, avg_loss_pct, conservative=conservative
        )
        
        # 2. Calculer capital à allouer (limiter au max du capital)
        capital_for_ticker = self.initial_capital * kelly_f
        
        # 3. Calculer nombre d'actions
        num_shares = int(capital_for_ticker / current_stock_price)
        actual_capital = num_shares * current_stock_price
        
        return num_shares, actual_capital, kelly_f
    
    def calculate_multi_ticker_allocation(self,
                                         portfolio: Dict[str, Dict],
                                         total_capital: Optional[float] = None) -> Dict[str, Dict]:
        """
        Alloue le capital entre plusieurs tickers.
        
        Args:
            portfolio: Dict avec structure:
                {
                    'AAPL': {
                        'price': 185.50,
                        'win_rate': 0.75,
                        'avg_win_pct': 0.05,
                        'avg_loss_pct': -0.02,
                        'weight': None  # Calculé automatiquement
                    },
                    ...
                }
            total_capital: Capital total à allouer (default: self.initial_capital)
            
        Returns:
            Portfolio mis à jour avec allocations et tailles de position
        """
        if total_capital is None:
            total_capital = self.initial_capital
        
        # 1. Calculer fractions Kelly individuelles
        kelly_fractions = {}
        for ticker, params in portfolio.items():
            f = self.calculate_kelly_fraction(
                params['win_rate'],
                params['avg_win_pct'],
                params['avg_loss_pct'],
                conservative=True
            )
            kelly_fractions[ticker] = f
        
        # 2. Normaliser pour respecter levier maximum
        total_kelly = sum(kelly_fractions.values())
        
        if total_kelly > 0:
            # Vérifier levier
            if total_kelly > self.max_portfolio_leverage:
                # Réduire proportionnellement
                scaling_factor = self.max_portfolio_leverage / total_kelly
                kelly_fractions = {k: v * scaling_factor for k, v in kelly_fractions.items()}
        
        # 3. Calculer allocations finales
        allocations = {}
        for ticker, kelly_f in kelly_fractions.items():
            params = portfolio[ticker]
            capital_allocated = total_capital * kelly_f
            num_shares = int(capital_allocated / params['price'])
            actual_capital = num_shares * params['price']
            
            allocations[ticker] = {
                'kelly_fraction': kelly_f,
                'allocated_capital': actual_capital,
                'num_shares': num_shares,
                'price': params['price'],
                'win_rate': params['win_rate'],
                'leverage_contribution': kelly_f
            }
        
        allocations['total'] = {
            'allocated_capital': sum(a['allocated_capital'] for a in allocations.values() if a != 'total'),
            'total_portfolio_leverage': sum(a['leverage_contribution'] for a in allocations.values() if a != 'total'),
            'cash_remaining': total_capital - sum(a['allocated_capital'] for a in allocations.values() if a != 'total')
        }
        
        return allocations
    
    def calculate_risk_per_trade(self,
                                num_shares: int,
                                entry_price: float,
                                stop_loss_pct: float) -> float:
        """
        Calcule le risque dollar par trade.
        
        Args:
            num_shares: Nombre d'actions
            entry_price: Prix d'entrée
            stop_loss_pct: Stop loss en pourcent (ex: -0.02 = -2%)
            
        Returns:
            Risque en dollars
        """
        position_value = num_shares * entry_price
        risk_amount = position_value * abs(stop_loss_pct)
        return risk_amount
    
    def calculate_reward_per_trade(self,
                                  num_shares: int,
                                  entry_price: float,
                                  take_profit_pct: float) -> float:
        """
        Calcule le profit potentiel par trade.
        
        Args:
            num_shares: Nombre d'actions
            entry_price: Prix d'entrée
            take_profit_pct: Take profit en pourcent (ex: 0.05 = +5%)
            
        Returns:
            Profit potentiel en dollars
        """
        position_value = num_shares * entry_price
        profit_amount = position_value * take_profit_pct
        return profit_amount
    
    def calculate_expected_value(self,
                                win_rate: float,
                                avg_win: float,
                                avg_loss: float) -> float:
        """
        Calcule la valeur espérée d'une stratégie.
        
        Args:
            win_rate: Taux de gain (0-1)
            avg_win: Gain moyen par trade gagnant ($)
            avg_loss: Perte moyenne par trade perdant ($, négatif)
            
        Returns:
            Valeur espérée par trade ($)
        """
        ev = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        return ev


class RiskManager:
    """Gère les règles de risque et limites de trading"""
    
    def __init__(self):
        self.max_daily_loss_pct = 0.02  # Max -2% par jour
        self.max_weekly_loss_pct = 0.05  # Max -5% par semaine
        self.max_monthly_loss_pct = 0.10  # Max -10% par mois
        self.max_consecutive_losses = 5  # Max 5 pertes consécutives
        self.min_win_rate_threshold = 0.40  # Min 40% de win rate
        self.max_pos_per_ticker = 3  # Max 3 positions ouvertes par ticker
        self.max_total_positions = 10  # Max 10 positions totales
        self.max_leverage = 2.0  # Max levier 2x
    
    def check_daily_drawdown(self, 
                            current_equity: float,
                            starting_equity: float) -> Tuple[bool, float]:
        """Vérifie si le drawdown quotidien est acceptable"""
        daily_loss = (starting_equity - current_equity) / starting_equity
        ok = daily_loss <= self.max_daily_loss_pct
        return ok, daily_loss
    
    def check_consecutive_losses(self, 
                                last_n_trades: list) -> Tuple[bool, int]:
        """Compte les pertes consécutives"""
        consecutive = 0
        for i in range(len(last_n_trades) - 1, -1, -1):
            if last_n_trades[i] < 0:
                consecutive += 1
            else:
                break
        
        ok = consecutive <= self.max_consecutive_losses
        return ok, consecutive
    
    def get_risk_status(self, 
                       current_equity: float,
                       starting_equity: float,
                       last_trades: list,
                       open_positions: int) -> Dict:
        """Retourne le statut global du risque"""
        daily_ok, daily_dd = self.check_daily_drawdown(current_equity, starting_equity)
        loss_ok, consecutive = self.check_consecutive_losses(last_trades)
        
        return {
            'daily_ok': daily_ok,
            'daily_drawdown': daily_dd,
            'loss_ok': loss_ok,
            'consecutive_losses': consecutive,
            'positions_ok': open_positions <= self.max_total_positions,
            'open_positions': open_positions,
            'all_ok': daily_ok and loss_ok and (open_positions <= self.max_total_positions)
        }


# ============ EXEMPLE D'UTILISATION ============

if __name__ == "__main__":
    # Initialiser le calculateur Kelly
    kelly = KellyCalculator(initial_capital=100000)
    
    # Exemple: GOOGL avec paramètres optimisés
    # Win rate: 75.6%, Avg win: +11%, Avg loss: -2%
    shares, capital, kelly_f = kelly.calculate_position_size(
        ticker='GOOGL',
        win_rate=0.756,  # 75.6% win rate
        avg_win_pct=0.11,  # +11% rendement moyen
        avg_loss_pct=-0.02,  # -2% perte moyenne
        current_stock_price=190.50  # Prix GOOGL
    )
    
    print(f"GOOGL Position Sizing:")
    print(f"  Kelly Fraction: {kelly_f:.4f} ({kelly_f*100:.2f}%)")
    print(f"  Shares to buy: {shares}")
    print(f"  Capital allocated: ${capital:,.2f}")
    print(f"  Risk per trade: ${kelly.calculate_risk_per_trade(shares, 190.50, -0.02):,.2f}")
    print(f"  Reward per trade: ${kelly.calculate_reward_per_trade(shares, 190.50, 0.11):,.2f}")
    
    # Multi-ticker allocation
    print("\n" + "="*60)
    print("Multi-Ticker Allocation:")
    portfolio = {
        'AAPL': {
            'price': 185.50,
            'win_rate': 0.50,
            'avg_win_pct': 0.05,
            'avg_loss_pct': -0.02,
        },
        'GOOGL': {
            'price': 190.50,
            'win_rate': 0.756,
            'avg_win_pct': 0.11,
            'avg_loss_pct': -0.02,
        },
        'MSFT': {
            'price': 440.00,
            'win_rate': 1.0,
            'avg_win_pct': 0.0184,
            'avg_loss_pct': -0.02,
        },
        'TSLA': {
            'price': 250.00,
            'win_rate': 0.525,
            'avg_win_pct': 0.057,
            'avg_loss_pct': -0.02,
        },
    }
    
    allocations = kelly.calculate_multi_ticker_allocation(portfolio)
    
    for ticker, alloc in allocations.items():
        if ticker != 'total':
            print(f"\n{ticker}:")
            print(f"  Kelly Fraction: {alloc['kelly_fraction']:.4f}")
            print(f"  Num Shares: {alloc['num_shares']}")
            print(f"  Capital: ${alloc['allocated_capital']:,.2f}")
    
    total = allocations['total']
    print(f"\nTotal Allocation:")
    print(f"  Capital invested: ${total['allocated_capital']:,.2f}")
    print(f"  Cash remaining: ${total['cash_remaining']:,.2f}")
    print(f"  Portfolio leverage: {total['total_portfolio_leverage']:.2f}x")
