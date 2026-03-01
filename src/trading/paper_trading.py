"""
Paper Trading Simulator
=======================

Simule le trading en papier pour tester les stratégies avant le trading réel.
Utilise les prix réels mais pas d'argent réel.

Features:
- Simulation complète d'ordres d'achat/vente
- Tracking des positions ouvertes
- Calcul P&L en temps réel
- Commission et slippage simulés
- Journalisation de tous les trades
- Statistiques de performance
"""

import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import sys

# Ajouter src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading.kelly_calculator import KellyCalculator, RiskManager


class Trade:
    """Représente un trade (achat/vente)"""
    
    def __init__(self, 
                 trade_id: str,
                 ticker: str,
                 side: str,  # 'BUY' ou 'SELL'
                 shares: int,
                 price: float,
                 timestamp: datetime,
                 order_type: str = 'MARKET',
                 commission: float = 0.0):
        self.trade_id = trade_id
        self.ticker = ticker
        self.side = side
        self.shares = shares
        self.price = price
        self.timestamp = timestamp
        self.order_type = order_type
        self.commission = commission
        self.gross_value = shares * price
        self.net_value = self.gross_value - commission
    
    def to_dict(self) -> Dict:
        return {
            'trade_id': self.trade_id,
            'ticker': self.ticker,
            'side': self.side,
            'shares': self.shares,
            'price': f"{self.price:.2f}",
            'gross_value': f"{self.gross_value:,.2f}",
            'commission': f"{self.commission:,.2f}",
            'net_value': f"{self.net_value:,.2f}",
            'timestamp': self.timestamp.isoformat()
        }


class Position:
    """Représente une position ouverte"""
    
    def __init__(self,
                 ticker: str,
                 entry_price: float,
                 num_shares: int,
                 entry_time: datetime,
                 stop_loss_pct: float,
                 take_profit_pct: float):
        self.ticker = ticker
        self.entry_price = entry_price
        self.num_shares = num_shares
        self.entry_time = entry_time
        self.current_price = entry_price
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        # Niveaux
        self.stop_loss_price = entry_price * (1 + stop_loss_pct)
        self.take_profit_price = entry_price * (1 + take_profit_pct)
    
    def update_price(self, current_price: float):
        """Met à jour le prix actuel"""
        self.current_price = current_price
    
    def get_pnl(self) -> Tuple[float, float]:
        """Retourne (dollar_pnl, percent_pnl)"""
        position_value = self.num_shares * self.current_price
        entry_value = self.num_shares * self.entry_price
        dollar_pnl = position_value - entry_value
        percent_pnl = dollar_pnl / entry_value if entry_value > 0 else 0
        return dollar_pnl, percent_pnl
    
    def is_stop_hit(self) -> bool:
        """Vérifie si le stop loss est hit"""
        return self.current_price <= self.stop_loss_price
    
    def is_target_hit(self) -> bool:
        """Vérifie si le take profit est hit"""
        return self.current_price >= self.take_profit_price
    
    def to_dict(self) -> Dict:
        dollar_pnl, percent_pnl = self.get_pnl()
        return {
            'ticker': self.ticker,
            'entry_price': f"{self.entry_price:.2f}",
            'current_price': f"{self.current_price:.2f}",
            'num_shares': self.num_shares,
            'position_value': f"{self.num_shares * self.current_price:,.2f}",
            'pnl_dollar': f"{dollar_pnl:,.2f}",
            'pnl_percent': f"{percent_pnl*100:.2f}%",
            'stop_loss': f"{self.stop_loss_price:.2f}",
            'take_profit': f"{self.take_profit_price:.2f}",
            'hours_open': round((datetime.now() - self.entry_time).total_seconds() / 3600, 1)
        }


class PaperTradingSimulator:
    """Simulateur de trading en papier"""
    
    def __init__(self,
                 initial_capital: float = 100000.0,
                 commission_pct: float = 0.001,  # 0.1% commission
                 slippage_pct: float = 0.0005):  # 0.05% slippage
        """
        Args:
            initial_capital: Capital initial
            commission_pct: Commission en % (default 0.1%)
            slippage_pct: Slippage en % (default 0.05%)
        """
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.commission_pct = commission_pct
        self.slippage_pct = slippage_pct
        
        # État
        self.positions: Dict[str, Position] = {}  # ticker -> Position
        self.trade_history: List[Trade] = []
        self.closed_trades: List[Dict] = []
        self.account_history: List[Dict] = []
        
        # Calculateurs
        self.kelly = KellyCalculator(initial_capital)
        self.risk_manager = RiskManager()
        
        # Tracking
        self.start_time = datetime.now()
        self.trade_counter = 0
    
    def get_account_value(self) -> Tuple[float, float]:
        """Retourne (gross_value, net_equity)"""
        positions_value = sum(pos.num_shares * pos.current_price 
                            for pos in self.positions.values())
        gross_value = self.current_cash + positions_value
        return gross_value, self.current_cash
    
    def get_open_positions(self) -> List[Dict]:
        """Retourne la liste des positions ouvertes"""
        return [pos.to_dict() for pos in self.positions.values()]
    
    def get_portfolio_summary(self) -> Dict:
        """Retourne un résumé du portefeuille"""
        gross_value, cash = self.get_account_value()
        entry_value = sum(pos.num_shares * pos.entry_price 
                         for pos in self.positions.values())
        return {
            'start_capital': f"${self.initial_capital:,.2f}",
            'current_equity': f"${gross_value:,.2f}",
            'cash': f"${cash:,.2f}",
            'invested': f"${gross_value - cash:,.2f}",
            'portfolio_pnl': f"${gross_value - self.initial_capital:,.2f}",
            'portfolio_return': f"{((gross_value - self.initial_capital) / self.initial_capital * 100):.2f}%",
            'open_positions': len(self.positions),
            'closed_trades': len(self.closed_trades),
            'total_trades': len(self.trade_history),
        }
    
    def buy(self,
            ticker: str,
            num_shares: int,
            current_price: float,
            stop_loss_pct: float,
            take_profit_pct: float,
            reason: str = "") -> Tuple[bool, str]:
        """
        Ouvre une position long.
        
        Returns:
            (success, message)
        """
        # Vérifier qu'il n'y a pas déjà une position
        if ticker in self.positions:
            return False, f"Position {ticker} already open"
        
        # Appliquer slippage
        entry_price = current_price * (1 + self.slippage_pct)
        position_value = num_shares * entry_price
        commission = position_value * self.commission_pct
        total_cost = position_value + commission
        
        # Vérifier qu'on a assez de cash
        if total_cost > self.current_cash:
            return False, f"Insufficient cash: need ${total_cost:,.2f}, have ${self.current_cash:,.2f}"
        
        # Créer la position
        pos = Position(
            ticker=ticker,
            entry_price=entry_price,
            num_shares=num_shares,
            entry_time=datetime.now(),
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct
        )
        
        # Créer le trade
        self.trade_counter += 1
        trade = Trade(
            trade_id=f"TRADE_{self.trade_counter:06d}",
            ticker=ticker,
            side='BUY',
            shares=num_shares,
            price=entry_price,
            timestamp=datetime.now(),
            commission=commission
        )
        
        # Mettre à jour le compte
        self.positions[ticker] = pos
        self.current_cash -= total_cost
        self.trade_history.append(trade)
        
        return True, f"Bought {num_shares} shares of {ticker} @ ${entry_price:.2f}"
    
    def sell(self,
             ticker: str,
             current_price: float,
             reason: str = "") -> Tuple[bool, str, Optional[Dict]]:
        """
        Ferme une position long.
        
        Returns:
            (success, message, closed_trade_dict)
        """
        # Vérifier la position existe
        if ticker not in self.positions:
            return False, f"No open position for {ticker}", None
        
        pos = self.positions[ticker]
        
        # Appliquer slippage
        exit_price = current_price * (1 - self.slippage_pct)
        position_value = pos.num_shares * exit_price
        commission = position_value * self.commission_pct
        net_proceeds = position_value - commission
        
        # Calculer P&L
        entry_value = pos.num_shares * pos.entry_price
        pnl = net_proceeds - entry_value
        pnl_pct = pnl / entry_value if entry_value > 0 else 0
        
        # Créer le trade de fermeture
        self.trade_counter += 1
        trade = Trade(
            trade_id=f"TRADE_{self.trade_counter:06d}",
            ticker=ticker,
            side='SELL',
            shares=pos.num_shares,
            price=exit_price,
            timestamp=datetime.now(),
            commission=commission
        )
        
        # Enregistrer le trade fermé
        closed = {
            'ticker': ticker,
            'entry_price': pos.entry_price,
            'exit_price': exit_price,
            'shares': pos.num_shares,
            'entry_time': pos.entry_time.isoformat(),
            'exit_time': datetime.now().isoformat(),
            'pnl_dollar': round(pnl, 2),
            'pnl_percent': round(pnl_pct * 100, 2),
            'reason': reason,
            'duration_hours': round((datetime.now() - pos.entry_time).total_seconds() / 3600, 1)
        }
        
        # Mettre à jour le compte
        self.current_cash += net_proceeds
        del self.positions[ticker]
        self.trade_history.append(trade)
        self.closed_trades.append(closed)
        
        return True, f"Sold {pos.num_shares} shares of {ticker} @ ${exit_price:.2f} | P&L: ${pnl:,.2f}", closed
    
    def update_prices(self, prices: Dict[str, float]):
        """
        Met à jour les prix actuels de toutes les positions.
        
        Args:
            prices: Dict {ticker: price}
        """
        for ticker, price in prices.items():
            if ticker in self.positions:
                self.positions[ticker].update_price(price)
    
    def check_stop_and_targets(self, prices: Dict[str, float]) -> List[Tuple[str, str]]:
        """
        Vérifie si des stops ou targets sont hit.
        
        Returns:
            List de (ticker, action) tuples
        """
        actions = []
        
        for ticker, price in prices.items():
            if ticker not in self.positions:
                continue
            
            pos = self.positions[ticker]
            pos.update_price(price)
            
            if pos.is_stop_hit():
                actions.append((ticker, 'STOP_HIT'))
            elif pos.is_target_hit():
                actions.append((ticker, 'TARGET_HIT'))
        
        return actions
    
    def execute_auto_close(self, prices: Dict[str, float]) -> List[Dict]:
        """
        Exécute les fermetures automatiques (stop/target).
        
        Returns:
            List des closed trades
        """
        closed_list = []
        actions = self.check_stop_and_targets(prices)
        
        for ticker, action in actions:
            price = prices[ticker]
            reason = action
            success, msg, closed = self.sell(ticker, price, reason=reason)
            if success:
                closed_list.append(closed)
        
        return closed_list
    
    def save_session(self, filename: Optional[str] = None) -> str:
        """Sauvegarde la session de trading"""
        if filename is None:
            filename = f"paper_trading_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = Path(__file__).parent.parent.parent / "reports" / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        session_data = {
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'initial_capital': self.initial_capital,
            'portfolio_summary': self.get_portfolio_summary(),
            'open_positions': self.get_open_positions(),
            'closed_trades': self.closed_trades,
            'trade_history': [t.to_dict() for t in self.trade_history],
        }
        
        with open(filepath, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return str(filepath)


# ============ EXEMPLE D'UTILISATION ============

if __name__ == "__main__":
    # Initialiser le simulateur
    sim = PaperTradingSimulator(initial_capital=100000)
    
    print("="*70)
    print("PAPER TRADING SIMULATOR - Example Session")
    print("="*70)
    
    # Trade 1: Achat GOOGL
    success, msg = sim.buy(
        ticker='GOOGL',
        num_shares=50,
        current_price=190.50,
        stop_loss_pct=-0.02,
        take_profit_pct=0.07
    )
    print(f"\n1. {msg}")
    print(f"   Portfolio: {sim.get_portfolio_summary()}")
    
    # Trade 2: Achat MSFT
    success, msg = sim.buy(
        ticker='MSFT',
        num_shares=15,
        current_price=440.00,
        stop_loss_pct=-0.02,
        take_profit_pct=0.05
    )
    print(f"\n2. {msg}")
    
    # Mettre à jour les prix (GOOGL +3%)
    print("\n3. Updating prices: GOOGL +3%")
    sim.update_prices({'GOOGL': 190.50 * 1.03, 'MSFT': 440.00})
    
    print("\n   Open Positions:")
    for pos in sim.get_open_positions():
        print(f"   - {pos}")
    
    # Vendre GOOGL
    success, msg, closed = sim.sell(
        ticker='GOOGL',
        current_price=190.50 * 1.03,
        reason='Manual exit'
    )
    print(f"\n4. {msg}")
    if closed:
        print(f"   Closed trade: {closed}")
    
    # Récapitulatif final
    print("\n" + "="*70)
    print("Final Portfolio Summary:")
    print("="*70)
    for k, v in sim.get_portfolio_summary().items():
        print(f"{k:20s}: {v}")
    
    print("\nOpen Positions:")
    for pos in sim.get_open_positions():
        print(f"  {pos['ticker']}: {pos['pnl_percent']} ({pos['position_value']})")
    
    print("\nClosed Trades:")
    for trade in sim.closed_trades:
        print(f"  {trade['ticker']}: {trade['pnl_percent']}% | ${trade['pnl_dollar']:,.2f}")
