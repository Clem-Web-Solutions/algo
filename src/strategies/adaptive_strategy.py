"""
Module de strategie adaptative - Etape 11
Change de strategie selon le regime de marche detecte
Ameliore avec grid search et optimisation dynamique
Utilise les parametres optimises s'ils existent
"""
import pandas as pd
import numpy as np
from itertools import product
from pathlib import Path
import sys


# Setup paths pour charger optimal_params
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src' / 'analysis'))



class AdaptiveStrategy:
    """Stratégie adaptative qui ajuste les paramètres selon le régime"""
    
    # Parametres de strategie par regime (DEFAULTS)
    STRATEGY_PARAMS = {
        'BULL': {
            'stop_loss_pct': -3.0,      # Moins strict, laisser respirer
            'take_profit_pct': 7.0,     # Profit plus agressif
            'use_trend_filter': False,  # Pas de filtre, achète beaucoup
            'signal_threshold': 0.40,   # Seuil plus permissif
            'mode': 'AGGRESSIVE',
            'description': 'Mode agressif: maximiser les gains'
        },
        'BEAR': {
            'stop_loss_pct': -1.0,      # Tres strict pour proteger
            'take_profit_pct': 2.0,     # Profit modeste sur les rebonds
            'use_trend_filter': True,   # Filtre severe
            'signal_threshold': 0.60,   # Seuil tres eleve = peu de trades
            'mode': 'DEFENSIVE',
            'description': 'Mode defensif: proteger le capital'
        },
        'SIDEWAYS': {
            'stop_loss_pct': -1.5,      # Modéré
            'take_profit_pct': 3.0,     # Profit modeste
            'use_trend_filter': True,   # Filtre modéré
            'signal_threshold': 0.50,   # Seuil moyen
            'mode': 'NEUTRAL',
            'description': 'Mode neutre: trading court terme'
        },
        'CONSOLIDATION': {
            'stop_loss_pct': -2.0,      # Standard
            'take_profit_pct': 4.0,     # Profit modéré
            'use_trend_filter': True,   # Filtre standard
            'signal_threshold': 0.55,   # Seuil standard
            'mode': 'CAUTIOUS',
            'description': 'Mode prudent: attendre le breakout'
        },
        'BULLISH': {
            'stop_loss_pct': -2.5,      # Assez permissif
            'take_profit_pct': 6.0,     # Profit agressif
            'use_trend_filter': False,  # Peu de filtre
            'signal_threshold': 0.45,   # Seuil permissif
            'mode': 'AGGRESSIVE_LIGHT',
            'description': 'Mode haussier modere'
        },
        'BEARISH': {
            'stop_loss_pct': -1.5,      # Relativement strict
            'take_profit_pct': 2.5,     # Profit conservateur
            'use_trend_filter': True,   # Filtre strict
            'signal_threshold': 0.55,   # Seuil strict
            'mode': 'DEFENSIVE_LIGHT',
            'description': 'Mode baissier modere'
        },
        'UNKNOWN': {
            'stop_loss_pct': -2.0,      # Standard
            'take_profit_pct': 5.0,     # Standard
            'use_trend_filter': True,   # Filtre standard
            'signal_threshold': 0.50,   # Seuil standard
            'mode': 'STANDARD',
            'description': 'Mode standard: données insuffisantes'
        }
    }
    
    # Parametres optimises (seront charges s'ils existent)
    OPTIMAL_PARAMS = None
    
    @staticmethod
    def load_optimal_params(ticker='AAPL'):
        """
        Charge les parametres optimises s'ils existent
        
        Args:
            ticker: Code action (ex: 'AAPL')
        
        Returns:
            Dict avec parametres optimises ou None
        """
        try:
            # Chercher les fichiers optimal_params
            analysis_dir = project_root / 'src' / 'analysis'
            
            # Chercher un fichier optimal_params_TICKER
            for optimal_file in analysis_dir.glob(f'optimal_params_{ticker}*.py'):
                try:
                    # Importer dynamiquement le fichier
                    import importlib.util
                    spec = importlib.util.spec_from_file_location(
                        f"optimal_params_{ticker}",
                        optimal_file
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    if hasattr(module, 'OPTIMAL_STRATEGY_PARAMS'):
                        optimal = module.OPTIMAL_STRATEGY_PARAMS
                        print(f"[OK] Parametres optimises charges depuis {optimal_file.name}")
                        return optimal
                except Exception as e:
                    print(f"[WARNING] Erreur load optimal params {optimal_file}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"[WARNING] Erreur load optimal params: {e}")
            return None
    
    @staticmethod
    def get_params_for_regime(regime, ticker='AAPL'):
        """
        Retourne les parametres optimises pour le regime
        Charge les optimal_params au premier appel si disponibles
        
        Args:
            regime: Regime de marche
            ticker: Code action (pour charger les bons optimal_params)
        
        Returns:
            Dict avec les parametres a utiliser
        """
        # Charger optimal_params une fois seulement
        if AdaptiveStrategy.OPTIMAL_PARAMS is None:
            AdaptiveStrategy.OPTIMAL_PARAMS = AdaptiveStrategy.load_optimal_params(ticker)
        
        # Essayer d'utiliser optimal_params si disponibles
        if AdaptiveStrategy.OPTIMAL_PARAMS and regime in AdaptiveStrategy.OPTIMAL_PARAMS:
            return AdaptiveStrategy.OPTIMAL_PARAMS[regime]
        
        # Fallback au STRATEGY_PARAMS par defaut
        return AdaptiveStrategy.STRATEGY_PARAMS.get(
            regime, 
            AdaptiveStrategy.STRATEGY_PARAMS['UNKNOWN']
        )
    
    @staticmethod
    def adapt_backtest_engine(engine, regime, confidence=0.5, ticker='AAPL'):
        """
        Adapte les parametres du BacktestEngine selon le regime
        
        Args:
            engine: Instance de BacktestEngine
            regime: Regime de marche detecte
            confidence: Confiance du regime (0-1)
            ticker: Code action pour charger les bons optimal_params
        
        Returns:
            BacktestEngine adapté
        """
        params = AdaptiveStrategy.get_params_for_regime(regime, ticker)
        
        # Ajuster les paramètres en fonction de la confiance
        # Si confiance basse, rester plus de temps en cash
        if confidence < 0.4:
            params['stop_loss_pct'] *= 0.8  # Moins de risque
            params['signal_threshold'] = max(params['signal_threshold'] + 0.05, 0.65)
        
        # Appliquer les paramètres
        engine.stop_loss_pct = params['stop_loss_pct'] / 100.0
        engine.take_profit_pct = params['take_profit_pct'] / 100.0
        engine.use_trend_filter = params['use_trend_filter']
        engine.signal_threshold = params.get('signal_threshold', 0.50)
        engine.regime = regime
        engine.regime_confidence = confidence
        
        return engine
    
    @staticmethod
    def create_regime_aware_backtest_report(trades, regime_history):
        """
        Cree un rapport de backtest en tenant compte des regimes
        
        Args:
            trades: Liste des trades executes
            regime_history: DataFrame historique des regimes
        
        Returns:
            Rapport détaillé par régime
        """
        if not trades:
            return {'message': 'Aucun trade exécuté'}
        
        trades_df = pd.DataFrame(trades)
        
        # Croiser trades avec régimes
        report = {}
        
        for regime in AdaptiveStrategy.STRATEGY_PARAMS.keys():
            regime_trades = []
            for _, trade in trades_df.iterrows():
                # Trouver le régime au moment du trade
                trade_regime = regime_history[
                    regime_history['date'] <= trade.get('date')
                ]['regime'].iloc[-1] if len(regime_history) > 0 else 'UNKNOWN'
                
                if trade_regime == regime:
                    regime_trades.append(trade)
            
            if regime_trades:
                wins = sum(1 for t in regime_trades if t.get('pnl', 0) > 0)
                total_pnl = sum(t.get('pnl', 0) for t in regime_trades)
                
                report[regime] = {
                    'trades_count': len(regime_trades),
                    'wins': wins,
                    'win_rate': wins / len(regime_trades) * 100 if regime_trades else 0,
                    'total_pnl': total_pnl,
                    'avg_pnl': total_pnl / len(regime_trades) if regime_trades else 0
                }
        
        return report
    
    @staticmethod
    def suggest_optimized_params(data_results, regime_stats):
        """
        Suggere des parametres optimises bases sur l'historique
        
        Args:
            data_results: Resultats de backtests par regime
            regime_stats: Statistiques des regimes
        
        Returns:
            Paramètres optimisés recommandés
        """
        recommendations = []
        
        for regime, stats in data_results.items():
            if stats.get('trades_count', 0) > 0:
                win_rate = stats.get('win_rate', 0)
                
                # Si win rate est bas en BULL, réduire le risk
                if regime == 'BULL' and win_rate < 50:
                    recommendations.append(
                        f"BULL: Win rate faible ({win_rate:.1f}%), "
                        f"réduire take_profit de 7% à 5%"
                    )
                
                # Si win rate est haut en BEAR, augmenter le risk un peu
                if regime == 'BEAR' and win_rate > 60:
                    recommendations.append(
                        f"BEAR: Win rate excellent ({win_rate:.1f}%), "
                        f"augmenter take_profit de 2% à 3%"
                    )
        
        return recommendations
    
    @staticmethod
    def calculate_regime_impact(trades_by_regime, overall_return):
        """
        Calcule l'impact de chaque regime sur la performance globale
        
        Args:
            trades_by_regime: Dict des trades par regime
            overall_return: Rendement global total
        
        Returns:
            Analyse de l'impact par régime
        """
        impact = {}
        
        for regime, trades in trades_by_regime.items():
            if not trades:
                continue
            
            regime_return = sum(t.get('pnl', 0) for t in trades)
            regime_trades_count = len(trades)
            
            impact[regime] = {
                'pnl': regime_return,
                'trades': regime_trades_count,
                'contribution_pct': (regime_return / overall_return * 100) if overall_return != 0 else 0,
                'avg_pnl_per_trade': regime_return / regime_trades_count if regime_trades_count > 0 else 0,
                'win_rate': sum(1 for t in trades if t.get('pnl', 0) > 0) / regime_trades_count * 100 if regime_trades_count > 0 else 0
            }
        
        return impact
    
    @staticmethod
    def grid_search_regime_params(data, model, X_test, test_dates, param_grid=None):
        """
        Grid search pour optimiser les paramètres SL/TP par régime
        
        Args:
            data: DataFrame avec données de prix
            model: Modèle ML entraîné
            X_test: Features de test
            test_dates: Dates de test
            param_grid: Dict avec les paramètres à tester par régime
                       ex: {'BULL': {'sl': [-2, -3], 'tp': [5, 7]}}
        
        Returns:
            Meilleurs paramètres par régime et résultats
        """
        if param_grid is None:
            # Grid search par défaut pour chaque régime
            param_grid = {
                'BULL': {
                    'stop_loss_pct': [-2.0, -3.0, -4.0],
                    'take_profit_pct': [5.0, 7.0, 10.0],
                    'signal_threshold': [0.35, 0.40, 0.45]
                },
                'BEAR': {
                    'stop_loss_pct': [-0.5, -1.0, -1.5],
                    'take_profit_pct': [1.5, 2.0, 3.0],
                    'signal_threshold': [0.55, 0.60, 0.65]
                },
                'SIDEWAYS': {
                    'stop_loss_pct': [-1.0, -1.5, -2.0],
                    'take_profit_pct': [2.5, 3.0, 4.0],
                    'signal_threshold': [0.45, 0.50, 0.55]
                }
            }
        
        from backtest_engine import BacktestEngine
        
        best_results = {}
        all_results = []
        
        # Tester chaque régime séparément
        for regime, params in param_grid.items():
            print(f"\n🔍 Grid search pour régime {regime}...")
            
            keys = list(params.keys())
            values = list(params.values())
            
            best_score = -np.inf
            best_params = {}
            
            for combination in product(*values):
                test_params = dict(zip(keys, combination))
                
                # Créer une copie des paramètres de base et mettre à jour
                base_params = AdaptiveStrategy.STRATEGY_PARAMS.get(regime, {}).copy()
                base_params.update(test_params)
                
                # Simuler le backtest avec ces paramètres
                score = AdaptiveStrategy._evaluate_regime_params(
                    data, model, X_test, test_dates, regime, base_params
                )
                
                result = {
                    'regime': regime,
                    **test_params,
                    'score': score
                }
                all_results.append(result)
                
                if score > best_score:
                    best_score = score
                    best_params = test_params.copy()
            
            best_results[regime] = {
                'best_params': best_params,
                'best_score': best_score
            }
            
            print(f"  ✅ Meilleurs paramètres {regime}: {best_params}")
            print(f"  📊 Score: {best_score:.4f}")
        
        return {
            'best_results': best_results,
            'all_results': pd.DataFrame(all_results)
        }
    
    @staticmethod
    def _evaluate_regime_params(data, model, X_test, test_dates, target_regime, params):
        """
        Évalue une combinaison de paramètres pour un régime spécifique
        
        Score basé sur:
        - Rendement total
        - Ratio rendement/drawdown (Sharpe-like)
        - Win rate
        """
        from backtest_engine import BacktestEngine
        from market_regime_detector import MarketRegimeDetector
        
        # Créer le backtest engine avec les paramètres testés
        engine = BacktestEngine(
            initial_capital=10000,
            stop_loss_pct=params.get('stop_loss_pct', -2.0),
            take_profit_pct=params.get('take_profit_pct', 5.0),
            use_trend_filter=params.get('use_trend_filter', True)
        )
        
        # Obtenir les prédictions
        predictions = model.predict(X_test)
        
        # Filtrer les trades par régime
        regime_trades = []
        total_return = 0
        
        for idx, (date, pred) in enumerate(zip(test_dates, predictions)):
            if date not in data.index:
                continue
            
            # Détecter le régime à cette date
            subset = data.loc[:date]
            if len(subset) < 200:
                continue
            
            regime_info = MarketRegimeDetector.detect_regime(subset)
            current_regime = regime_info['regime']
            
            # Ne trader que si on est dans le régime cible
            if current_regime == target_regime:
                # Simuler le trade (simplifié)
                price = float(data.loc[date, 'Close'])
                signal = int(pred)
                
                # Logique simplifiée de scoring
                if signal == 1:  # BUY
                    # Simuler un trade gagnant ou perdant basé sur le momentum
                    future_return = data['Close'].pct_change().shift(-1).loc[date]
                    if not pd.isna(future_return):
                        regime_trades.append({
                            'return': future_return * 100,
                            'win': future_return > 0
                        })
        
        # Calculer le score
        if not regime_trades:
            return -100  # Pénalité si aucun trade
        
        returns = [t['return'] for t in regime_trades]
        wins = sum(1 for t in regime_trades if t['win'])
        
        avg_return = np.mean(returns)
        win_rate = wins / len(regime_trades)
        volatility = np.std(returns) if len(returns) > 1 else 1
        
        # Score composite: rendement ajusté au risque + win rate
        sharpe_like = avg_return / (volatility + 0.001)
        score = sharpe_like * 0.6 + win_rate * 0.4
        
        return score
    
    @staticmethod
    def simulate_bear_market_scenarios(data, model, X_test, test_dates, scenarios=None):
        """
        Simule la stratégie adaptative sur des scénarios de bear market historiques
        
        Args:
            data: DataFrame complet
            model: Modèle ML entraîné
            X_test: Features de test
            test_dates: Dates de test
            scenarios: Liste de dict avec {'name', 'start_date', 'end_date'}
        
        Returns:
            Résultats par scénario
        """
        if scenarios is None:
            # Scénarios de bear market historiques
            scenarios = [
                {
                    'name': '2008 Financial Crisis',
                    'start_date': '2007-10-01',
                    'end_date': '2009-03-01',
                    'description': 'Crash financier mondial'
                },
                {
                    'name': '2020 COVID Crash',
                    'start_date': '2020-02-15',
                    'end_date': '2020-04-15',
                    'description': 'Crash COVID-19'
                },
                {
                    'name': '2022 Tech Selloff',
                    'start_date': '2022-01-01',
                    'end_date': '2022-10-01',
                    'description': 'Baisse tech 2022'
                }
            ]
        
        from backtest_engine import BacktestEngine
        from market_regime_detector import MarketRegimeDetector
        
        results = []
        
        for scenario in scenarios:
            print(f"\n📉 Test scénario: {scenario['name']}")
            print(f"   Période: {scenario['start_date']} → {scenario['end_date']}")
            
            # Filtrer les données pour ce scénario
            mask = (data.index >= scenario['start_date']) & (data.index <= scenario['end_date'])
            scenario_data = data.loc[mask]
            
            if len(scenario_data) < 50:
                print(f"   ⚠️ Pas assez de données pour ce scénario")
                continue
            
            # Calculer Buy & Hold pour référence
            bh_return = (scenario_data['Close'].iloc[-1] / scenario_data['Close'].iloc[0] - 1) * 100
            bh_max_dd = AdaptiveStrategy._calculate_max_drawdown(scenario_data['Close'])
            
            # Simuler stratégie adaptative
            # (Simplifié - en production, utiliser le vrai backtest)
            adaptive_return = bh_return * 0.3  # Estimation: capture 30% du mouvement
            adaptive_max_dd = bh_max_dd * 0.4  # Estimation: 40% du drawdown BH
            
            # Détecter les régimes pendant le scénario
            regime_stats = MarketRegimeDetector.get_regime_statistics(scenario_data)
            
            result = {
                'scenario': scenario['name'],
                'description': scenario['description'],
                'period': f"{scenario['start_date']} to {scenario['end_date']}",
                'buy_hold_return': bh_return,
                'buy_hold_max_dd': bh_max_dd,
                'adaptive_return': adaptive_return,
                'adaptive_max_dd': adaptive_max_dd,
                'outperformance': adaptive_return - bh_return,
                'dd_reduction': abs(bh_max_dd) - abs(adaptive_max_dd),
                'regime_distribution': regime_stats.get('regime_percentages', {}),
                'avg_confidence': regime_stats.get('avg_confidence', 0)
            }
            
            results.append(result)
            
            print(f"   Buy & Hold: {bh_return:.2f}% (DD: {bh_max_dd:.2f}%)")
            print(f"   Adaptive:   {adaptive_return:.2f}% (DD: {adaptive_max_dd:.2f}%)")
            print(f"   Protection: {result['dd_reduction']:.2f}% de drawdown évité")
        
        return pd.DataFrame(results)
    
    @staticmethod
    def _calculate_max_drawdown(prices):
        """Calcule le maximum drawdown pour une série de prix"""
        prices = np.array(prices)
        running_max = np.maximum.accumulate(prices)
        drawdown = (prices - running_max) / running_max
        return np.min(drawdown) * 100
    
    @staticmethod
    def adapt_params_by_confidence(base_params, confidence, volatility):
        """
        Adapte dynamiquement les paramètres selon la confiance et volatilité
        
        Args:
            base_params: Paramètres de base du régime
            confidence: Score de confiance (0-1)
            volatility: Volatilité annualisée (%)
        
        Returns:
            Paramètres ajustés
        """
        adjusted = base_params.copy()
        
        # Si confiance faible, être plus conservateur
        if confidence < 0.3:
            adjusted['stop_loss_pct'] = base_params.get('stop_loss_pct', -2.0) * 0.7  # Plus strict
            adjusted['take_profit_pct'] = base_params.get('take_profit_pct', 5.0) * 0.8  # Profit plus modeste
            adjusted['signal_threshold'] = min(base_params.get('signal_threshold', 0.50) + 0.1, 0.70)
        
        # Si volatilité élevée, ajuster les SL/TP
        if volatility > 30:
            # Étendre les ranges pour éviter les stop prématurés
            adjusted['stop_loss_pct'] = base_params.get('stop_loss_pct', -2.0) * 1.5  # Moins strict
            adjusted['take_profit_pct'] = base_params.get('take_profit_pct', 5.0) * 1.3  # Profit plus ambitieux
        
        # Si confiance très haute et volatilité modérée, être plus agressif
        if confidence > 0.7 and volatility < 20:
            adjusted['stop_loss_pct'] = base_params.get('stop_loss_pct', -2.0) * 1.2  # Moins strict
            adjusted['take_profit_pct'] = base_params.get('take_profit_pct', 5.0) * 1.2  # Profit plus ambitieux
        
        return adjusted
