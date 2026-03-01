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

import pandas as pd
import numpy as np
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
                self.regime_history = detector.get_regime_history(self.data)
            
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
                self.model.train(X_train, y_train, X_val=X_test, y_val=y_test)
                
                # Sauvegarder le modele sur disque
                model_path = str(project_root / 'models' / f'model_{self.ticker}.pkl')
                self.model.save(model_path)
                
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
            
            with self.error_handler.error_context("Backtest"):
                # Determiner le regime dominant sur la periode de test
                dominant_regime = 'UNKNOWN'
                if self.regime_history is not None and len(self.regime_history) > 0:
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

                # Seuil adaptatif : regime comme base, fallback si trop peu de BUY
                proba = self.model.predict_proba(self.X_test)[:, 1]
                threshold = signal_threshold_base
                if (proba >= threshold).mean() < 0.04:  # moins de 4% de BUY
                    threshold = max(0.30, float(np.percentile(proba, 80)))
                predictions = (proba >= threshold).astype(int)
                n_buy = int(predictions.sum())
                n_sell = int((predictions == 0).sum())
                self.logger.info(f"Predictions: {n_buy} BUY / {n_sell} SELL (seuil={threshold:.3f})")

                # Creer backtest engine avec parametres adaptatifs
                engine = BacktestEngine(
                    initial_capital=BACKTEST_CONFIG['initial_capital'],
                    position_size_pct=BACKTEST_CONFIG['position_size_pct'],
                    stop_loss_pct=adaptive_params['stop_loss_pct'],
                    take_profit_pct=adaptive_params['take_profit_pct'],
                    use_trend_filter=adaptive_params['use_trend_filter'],
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
        self.logger.info(f"Capital final: ${results.get('final_value', 0):.2f}")
    
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
                    f.write("[BACKTEST RESULTS]\n")
                    f.write(f"Rendement: {self.backtest_results.get('total_return_pct', 0):.2f}%\n")
                    f.write(f"Trades: {self.backtest_results.get('buy_trades', 0)} achats / {self.backtest_results.get('sell_trades', 0)} ventes\n")
                    f.write(f"Win Rate: {self.backtest_results.get('win_rate', 0):.1f}%\n")
                    f.write(f"Drawdown: {self.backtest_results.get('max_drawdown', 0):.2f}%\n")
                    f.write(f"Capital final: ${self.backtest_results.get('final_value', 0):.2f}\n")
                
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
