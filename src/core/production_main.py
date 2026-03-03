"""
Production Pipeline - Etape 10
Version prete pour production avec error handling, logging, config externalisee
"""
import os
import sys
from pathlib import Path

# Setup paths
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / 'src' / 'core'))
sys.path.insert(0, str(project_root / 'src' / 'strategies'))
sys.path.insert(0, str(project_root / 'src' / 'analysis'))

import json
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from config import (
    STRATEGY_CONFIG, DEFAULT_TICKERS, START_DATE, 
    BACKTEST_CONFIG, MODEL_CONFIG, REPORTING_CONFIG, LOG_DIR
)
from error_handler import (
    setup_logger, ErrorHandler, SystemHealthCheck,
    DataFetchException, BacktestException, ModelException
)
from data_fetcher import DataFetcher
from feature_engineering import FeatureEngineering
from trading_model import TradingModel
from backtest_engine import BacktestEngine
from adaptive_strategy import AdaptiveStrategy
from market_regime_detector import MarketRegimeDetector


class ProductionTradingPipeline:
    """Pipeline production avec error handling et logging robuste"""
    
    def __init__(self, ticker='AAPL', config=None, use_optimized_params=False):
        """
        Init pipeline
        
        Args:
            ticker: Code action
            config: Dict config optionnel
            use_optimized_params: Utiliser parametres optimises si disponibles
        """
        self.ticker = ticker
        self.config = config or {}
        self.use_optimized_params = use_optimized_params
        
        # Setup logging
        self.logger, self.log_file = setup_logger(
            f'pipeline_{ticker}',
            log_dir=str(LOG_DIR)
        )
        
        # Error handler
        self.error_handler = ErrorHandler(self.logger)
        
        # System health
        self.system_health = SystemHealthCheck(self.logger)
        
        # Components
        self.data = None
        self.model = None
        self.backtest_results = None
        self.regime_history = None
        self.X_test = None
        self.y_test = None
        self.test_dates = None
        
        self.logger.info(f"ProductionTradingPipeline initialise pour {ticker}")
    
    def run_system_checks(self):
        """Lance les verifications systeme"""
        self.logger.info("="*70)
        self.logger.info("VERIFICATIONS SYSTEME")
        self.logger.info("="*70)
        
        try:
            self.system_health.check_disk_space(min_gb=1)
            self.system_health.check_memory(max_pct=95)
            self.system_health.check_directories([
                str(project_root / 'data'),
                str(project_root / 'reports'),
                str(project_root / 'models')
            ])
            
            health_report = self.system_health.get_health_report()
            self.logger.info(health_report)
            
            return True
        except Exception as e:
            self.error_handler.handle_error(e, "System checks", critical=False)
            return False
    
    def fetch_data(self, start_date=None, end_date=None):
        """Telecharge donnees avec error handling"""
        self.logger.info("="*70)
        self.logger.info("[1/5] TELECHARGEMENT DONNEES")
        self.logger.info("="*70)
        
        try:
            start = start_date or START_DATE
            
            self.logger.info(f"Ticket: {self.ticker}")
            self.logger.info(f"Periode: {start} a {end_date or 'Aujourd hui'}")
            
            with self.error_handler.error_context("Telecharger donnees"):
                fetcher = DataFetcher()
                self.data = fetcher.fetch_stock_data(self.ticker, start, end_date)
            
            # Valider
            is_valid, error = self.error_handler.validate_data(
                self.data,
                min_rows=100,
                required_columns=['Close', 'Volume']
            )
            
            if not is_valid:
                raise DataFetchException(f"Donnees invalides: {error}")
            
            self.logger.info(f"OK - {len(self.data)} jours telechargees")
            return True
        
        except Exception as e:
            self.error_handler.handle_error(e, "Data fetch", critical=False)
            return False
    
    def create_features(self):
        """Cree features techniques avec error handling"""
        self.logger.info("\n[2/5] CREATION INDICATEURS TECHNIQUES")
        
        try:
            with self.error_handler.error_context("Creation features"):
                fe = FeatureEngineering()
                # Ajouter les indicateurs techniques
                self.data = fe.add_technical_indicators(self.data)
                # Creer la variable target
                self.data['Target'] = fe.create_target_variable(self.data)
            
            n_features = self.data.shape[1]
            self.logger.info(f"OK - {n_features} indicateurs crees")
            
            return True
        
        except Exception as e:
            self.error_handler.handle_error(e, "Feature creation", critical=False)
            return False
    
    def detect_regimes(self):
        """Detecte regimes de marche"""
        self.logger.info("\n[3/5] DETECTION REGIMES DE MARCHE")
        
        try:
            with self.error_handler.error_context("Regime detection"):
                detector = MarketRegimeDetector()
                # Passer periods=len(data) pour couvrir l'ensemble de l'historique.
                # Avec periods=60 (défaut), le regime_history ne couvre que les 60 derniers
                # jours, alors que test_dates[0] est ~20% des données en arrière (>100 jours).
                # train_regimes deviendrait vide → dominant_regime calculé sur la période de
                # TEST → lookahead réintroduit silencieusement (annulation du fix P7 Iter 1).
                self.regime_history = detector.get_regime_history(
                    self.data, periods=len(self.data)
                )
            
            if self.regime_history is not None:
                regimes = self.regime_history['regime'].value_counts()
                self.logger.info("Regimes detectes:")
                for regime, count in regimes.items():
                    pct = (count / len(self.regime_history)) * 100
                    self.logger.info(f"  {regime}: {count} ({pct:.1f}%)")
            
            return True
        
        except Exception as e:
            self.error_handler.handle_error(e, "Regime detection", critical=False)
            return False
    
    def train_model(self, model_type=None):
        """Entraîne le modele avec error handling"""
        self.logger.info("\n[4/5] ENTRAINEMENT MODELE")
        
        try:
            model_type = model_type or MODEL_CONFIG.get('default_model_type', 'gradient_boosting')
            
            self.logger.info(f"Type: {model_type}")
            
            with self.error_handler.error_context("Model training"):
                # Preparer les donnees pour l'entrainement
                fe = FeatureEngineering()
                X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(
                    self.data.dropna(), 
                    test_size=0.2
                )
                
                # Entraîner le modele
                self.model = TradingModel(model_type=model_type)
                cv_scores = self.model.train(X_train, y_train, X_val=X_test, y_val=y_test)
                self._cv_f1_mean = float(cv_scores.mean()) if cv_scores is not None and len(cv_scores) > 0 else 0.0

                # Sauvegarder le modele, le scaler et la liste exacte des features
                # Les trois fichiers doivent être en phase pour le live trading
                model_path = str(project_root / 'models' / f'model_{self.ticker}.pkl')
                scaler_path = str(project_root / 'models' / f'scaler_{self.ticker}.pkl')
                features_path = str(project_root / 'models' / f'features_{self.ticker}.json')
                self.model.save(model_path)
                joblib.dump(scaler, scaler_path)
                with open(features_path, 'w') as f:
                    json.dump(list(X_train.columns), f)
                self.logger.info(f"OK - Scaler + features ({len(X_train.columns)} cols) sauvegardes")

                # Validation interne (derniers 20% du train) pour threshold optimization et Kelly.
                # On NE touche pas X_test — cet ensemble reste vierge jusqu'au backtest final.
                val_split_idx = int(len(X_train) * 0.80)
                self._X_val = X_train.iloc[val_split_idx:]
                self._y_val = y_train.iloc[val_split_idx:]

                # Série Close complète (non scalée) pour calculer les retours forward
                self._close_prices_full = self.data['Close'].copy()

                # Sauvegarder pour backtest
                self.X_test = X_test
                self.y_test = y_test
                self.test_dates = X_test.index
            
            self.logger.info("OK - Modele entraine")
            return True
        
        except Exception as e:
            self.error_handler.handle_error(e, "Model training", critical=False)
            return False
    
    def run_backtest(self):
        """Lance backtest avec strategie adaptative selon le regime dominant"""
        self.logger.info("\n[5/5] BACKTEST")
        
        try:
            if not hasattr(self, 'X_test') or self.model is None:
                self.logger.error("Model ou test data non disponible")
                return False

            # ── Gate F1 ──────────────────────────────────────────────────────
            # Si le modèle ne généralise pas (CV F1 < 0.45), ne pas trader
            cv_f1 = getattr(self, '_cv_f1_mean', 0.0)
            if cv_f1 < 0.45:
                self.logger.warning(
                    f"[Gate F1] CV F1={cv_f1:.3f} < 0.45 — backtest skippé "
                    f"(modèle insuffisant pour {self.ticker} ce cycle)"
                )
                return False
            # ─────────────────────────────────────────────────────────────────

            with self.error_handler.error_context("Backtest"):
                # Determiner le regime dominant sur la periode d'ENTRAINEMENT uniquement
                # (évite le lookahead : ne pas utiliser le régime de la période de test pour choisir les params)
                dominant_regime = 'UNKNOWN'
                if self.regime_history is not None and len(self.regime_history) > 0:
                    train_cutoff = self.test_dates[0] if self.test_dates is not None and len(self.test_dates) > 0 else None
                    if train_cutoff is not None:
                        train_regimes = self.regime_history[self.regime_history['date'] < train_cutoff]
                        if len(train_regimes) > 0:
                            dominant_regime = train_regimes['regime'].value_counts().index[0]
                        else:
                            dominant_regime = self.regime_history['regime'].value_counts().index[0]
                    else:
                        dominant_regime = self.regime_history['regime'].value_counts().index[0]

                # Recuperer les parametres adaptatifs pour ce regime
                adaptive_params = AdaptiveStrategy.STRATEGY_PARAMS.get(
                    dominant_regime,
                    AdaptiveStrategy.STRATEGY_PARAMS['UNKNOWN']
                )
                signal_threshold_base = adaptive_params['signal_threshold']
                self.logger.info(f"Regime dominant: {dominant_regime} -> "
                                 f"SL={adaptive_params['stop_loss_pct']}% / "
                                 f"TP={adaptive_params['take_profit_pct']}% / "
                                 f"seuil_base={signal_threshold_base}")

                # ----------------------------------------------------------------
                # Optimisation du seuil + Kelly sur les données de VALIDATION
                # (validation = derniers 20% du train — X_test reste vierge)
                # ----------------------------------------------------------------
                try:
                    from ml_optimizer import (
                        optimize_signal_threshold, fractional_kelly,
                        compute_financial_metrics, _compute_forward_returns,
                    )
                except ImportError:
                    from .ml_optimizer import (
                        optimize_signal_threshold, fractional_kelly,
                        compute_financial_metrics, _compute_forward_returns,
                    )

                prediction_window = 5
                optimal_threshold = signal_threshold_base  # fallback si val indisponible
                kelly_position_pct = BACKTEST_CONFIG['position_size_pct']  # fallback
                val_fin_metrics = {}

                if hasattr(self, '_X_val') and self._X_val is not None and len(self._X_val) >= 10:
                    val_probas = self.model.predict_proba(self._X_val)[:, 1]
                    val_fwd = _compute_forward_returns(
                        self._close_prices_full, self._X_val.index, prediction_window
                    )
                    valid_mask = ~np.isnan(val_fwd)
                    if valid_mask.sum() >= 5:
                        optimal_threshold, thr_df = optimize_signal_threshold(
                            val_probas[valid_mask], val_fwd[valid_mask],
                            commission_pct=0.1, slippage_pct=0.05,
                        )
                        val_preds_opt = (val_probas[valid_mask] >= optimal_threshold).astype(int)
                        val_fin_metrics = compute_financial_metrics(
                            val_preds_opt, val_fwd[valid_mask]
                        )
                        kelly_position_pct = fractional_kelly(
                            win_rate=val_fin_metrics.get('win_rate', 0.5),
                            avg_win_pct=val_fin_metrics.get('avg_win_pct', 1.0),
                            avg_loss_pct=val_fin_metrics.get('avg_loss_pct', -1.0),
                            fraction=0.25,
                        )
                        self.logger.info(
                            f"[MLOpt] Seuil optimal (validation): {optimal_threshold:.3f} | "
                            f"Sharpe={val_fin_metrics.get('sharpe', 0):.3f} | "
                            f"PF={val_fin_metrics.get('profit_factor', 0):.3f} | "
                            f"Exp={val_fin_metrics.get('expectancy', 0):.3f}%"
                        )
                        self.logger.info(
                            f"[MLOpt] Kelly (quarter-fraction): {kelly_position_pct:.3f} | "
                            f"WR={val_fin_metrics.get('win_rate', 0):.1%}"
                        )
                        # ── Gate Expectancy ───────────────────────────────────
                        # Si la validation montre un setup perdant, ne pas trader
                        val_exp = val_fin_metrics.get('expectancy', 0)
                        if val_exp <= 0:
                            self.logger.warning(
                                f"[Gate Exp] Expectancy validation={val_exp:.3f}% ≤ 0 — "
                                f"backtest skippé pour {self.ticker} (setup perdant sur validation)"
                            )
                            return False
                        # ─────────────────────────────────────────────────────
                    else:
                        self.logger.warning("[MLOpt] Validation trop courte — seuil régime utilisé en fallback")
                else:
                    self.logger.warning("[MLOpt] Pas de données de validation — seuil régime utilisé en fallback")

                # Seuil final: threshold optimisé > override trainer > fallback régime
                threshold = optimal_threshold
                if hasattr(self, '_signal_threshold_override') and self._signal_threshold_override is not None:
                    threshold = self._signal_threshold_override
                    self.logger.info(f"[Trainer] Seuil override actif: {threshold:.3f}")

                proba = self.model.predict_proba(self.X_test)[:, 1]
                predictions = (proba >= threshold).astype(int)
                n_buy = int(predictions.sum())
                n_sell = int((predictions == 0).sum())
                buy_pct = n_buy / max(len(predictions), 1)
                self.logger.info(f"Predictions: {n_buy} BUY ({buy_pct:.1%}) / {n_sell} SELL (seuil={threshold:.3f})")
                if buy_pct < 0.02:
                    self.logger.warning(f"Peu de signaux BUY ({buy_pct:.1%}) — régime {dominant_regime} probablement défensif (normal)")

                # Appliquer l'override stop_loss du continuous_trainer si présent
                effective_sl = adaptive_params['stop_loss_pct']
                if hasattr(self, '_stop_loss_override') and self._stop_loss_override is not None:
                    effective_sl = self._stop_loss_override
                    self.logger.info(f"Stop loss override actif: {effective_sl}% (vs base {adaptive_params['stop_loss_pct']}%)")

                # Creer backtest engine avec Kelly position sizing
                engine = BacktestEngine(
                    initial_capital=BACKTEST_CONFIG['initial_capital'],
                    position_size_pct=kelly_position_pct,  # Kelly fractionnel (25%)
                    stop_loss_pct=effective_sl,
                    take_profit_pct=adaptive_params['take_profit_pct'],
                    use_trend_filter=adaptive_params['use_trend_filter'],
                    max_trades=20,  # Cap: limiter les commissions
                )

                # Executer le backtest
                self.backtest_results = engine.run_backtest(
                    data=self.data,
                    model=self.model,
                    X_test=self.X_test,
                    test_dates=self.test_dates,
                    predictions=predictions
                )
            
            if self.backtest_results:
                # Enrichir les résultats avec les métriques de validation et le sizing utilisé
                self.backtest_results.update({
                    'optimal_threshold': threshold,
                    'kelly_position_size': kelly_position_pct,
                    'val_sharpe': val_fin_metrics.get('sharpe', None),
                    'val_profit_factor': val_fin_metrics.get('profit_factor', None),
                    'val_expectancy': val_fin_metrics.get('expectancy', None),
                    'val_win_rate': val_fin_metrics.get('win_rate', None),
                })
                self.logger.info("OK - Backtest complete")
                self._log_backtest_results()
                return True
            else:
                self.error_handler.handle_warning("Backtest returned empty results", "Backtest")
                return False
        
        except Exception as e:
            self.error_handler.handle_error(e, "Backtest", critical=False)
            return False
    
    def _log_backtest_results(self):
        """Log les resultats backtest"""
        results = self.backtest_results
        
        self.logger.info("\n" + "="*70)
        self.logger.info("RESULTATS BACKTEST")
        self.logger.info("="*70)
        
        self.logger.info(f"Rendement total: {results.get('total_return_pct', 0):.2f}%")
        self.logger.info(f"Nombre trades: {results.get('buy_trades', 0)} achats / {results.get('sell_trades', 0)} ventes")
        self.logger.info(f"Taux reussite: {results.get('win_rate', 0):.1f}%")
        self.logger.info(f"Profit moyen: ${results.get('avg_profit', 0):.2f}")
        self.logger.info(f"Max drawdown: {results.get('max_drawdown', 0):.2f}%")
        self.logger.info(f"Sharpe ratio: {results.get('sharpe_ratio', 0):.3f}")
        self.logger.info(f"Commissions: ${results.get('total_commissions', 0):.2f}")
        self.logger.info(f"Capital final: ${results.get('final_value', 0):.2f}")
        # Métriques de validation (signal de qualité du modèle avant test)
        if results.get('val_sharpe') is not None:
            self.logger.info(
                f"[Validation] Sharpe={results.get('val_sharpe', 0):.3f} | "
                f"PF={results.get('val_profit_factor', 0):.3f} | "
                f"Exp={results.get('val_expectancy', 0):.3f}% | "
                f"Seuil={results.get('optimal_threshold', 0):.3f} | "
                f"Kelly={results.get('kelly_position_size', 0):.3f}"
            )
    
    def save_report(self):
        """Sauvegarde rapport execution"""
        try:
            report_file = (project_root / 'reports' / 
                          f'production_report_{self.ticker}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
            
            with open(report_file, 'w') as f:
                f.write("="*70 + "\n")
                f.write(f"PRODUCTION PIPELINE REPORT - {self.ticker}\n")
                f.write("="*70 + "\n\n")
                
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Log file: {self.log_file}\n\n")
                
                if self.backtest_results:
                    r = self.backtest_results
                    f.write("[BACKTEST RESULTS]\n")
                    f.write(f"Rendement: {r.get('total_return_pct', 0):.2f}%\n")
                    f.write(f"Trades: {r.get('buy_trades', 0)} achats / {r.get('sell_trades', 0)} ventes\n")
                    f.write(f"Win Rate: {r.get('win_rate', 0):.1f}%\n")
                    f.write(f"Drawdown Max: {r.get('max_drawdown', 0):.2f}%\n")
                    f.write(f"Sharpe Ratio: {r.get('sharpe_ratio', 0):.3f}\n")
                    f.write(f"Commissions totales: ${r.get('total_commissions', 0):.2f}\n")
                    f.write(f"Slippage total: ${r.get('total_slippage', 0):.2f}\n")
                    f.write(f"Capital final: ${r.get('final_value', 0):.2f}\n")
                    f.write(f"\n[ML OPTIMIZER — VALIDATION]\n")
                    f.write(f"Seuil optimal: {r.get('optimal_threshold', 'N/A')}\n")
                    f.write(f"Kelly sizing: {r.get('kelly_position_size', 'N/A')}\n")
                    if r.get('val_sharpe') is not None:
                        f.write(f"Sharpe validation: {r.get('val_sharpe', 0):.3f}\n")
                        f.write(f"Profit factor validation: {r.get('val_profit_factor', 0):.3f}\n")
                        f.write(f"Expectancy validation: {r.get('val_expectancy', 0):.3f}%\n")
                        f.write(f"Win rate validation: {r.get('val_win_rate', 0):.1%}\n")
                
                f.write(f"\n[ERRORS]\n")
                f.write(f"Total errors: {self.error_handler.error_count}\n")
                f.write(f"Total warnings: {self.error_handler.warning_count}\n")
            
            self.logger.info(f"Rapport sauvegarde: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde rapport: {e}")
    
    def run_complete_pipeline(self, start_date=None, end_date=None):
        """Lance le pipeline complet"""
        self.logger.info("\n" + "="*70)
        self.logger.info(f"[ROCKET] PRODUCTION PIPELINE - {self.ticker}")
        if end_date:
            self.logger.info(f"Fenetre: {start_date} -> {end_date}")
        self.logger.info("="*70)
        
        # Checks
        if not self.run_system_checks():
            self.logger.error("System checks failed")
            return False
        
        # Pipeline
        steps = [
            ('Data Fetch', self.fetch_data, {'start_date': start_date, 'end_date': end_date}),
            ('Features', self.create_features, {}),
            ('Regimes', self.detect_regimes, {}),
            ('Training', self.train_model, {}),
            ('Backtest', self.run_backtest, {}),
        ]
        
        results = {}
        for step_name, step_func, kwargs in steps:
            success = step_func(**kwargs)
            results[step_name] = 'OK' if success else 'FAILED'
            
            if not success:
                self.logger.error(f"Pipeline stopped at {step_name}")
                break
        
        # Save report
        self.save_report()
        
        # Summary
        self.logger.info("\n" + "="*70)
        self.logger.info("RESUME EXECUTION")
        self.logger.info("="*70)
        for step, status in results.items():
            icon = "[OK]" if status == "OK" else "[FAILED]"
            self.logger.info(f"{icon} {step}")
        
        return all(v == 'OK' for v in results.values())


def main():
    """Script principal pour execution"""
    
    # Pipeline pour chaque ticker
    tickers = DEFAULT_TICKERS  # Tous les tickers (AAPL, GOOGL, MSFT, TSLA)
    
    for ticker in tickers:
        pipeline = ProductionTradingPipeline(ticker)
        pipeline.run_complete_pipeline(start_date=START_DATE)


if __name__ == '__main__':
    main()
