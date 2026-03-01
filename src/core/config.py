"""
Configuration centralisee - Etape 10
Tous les parametres externes (pas de hard-coding)
Production-ready
"""
from pathlib import Path
import os

# ============================================================================
# PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
REPORTS_DIR = PROJECT_ROOT / 'reports'
LOG_DIR = REPORTS_DIR
MODELS_DIR = PROJECT_ROOT / 'models'

# S'assurer que les dossiers existent
for dir_path in [DATA_DIR, REPORTS_DIR, LOG_DIR, MODELS_DIR]:
    dir_path.mkdir(exist_ok=True, parents=True)


# ============================================================================
# DATA CONFIG
# ============================================================================
DATA_CONFIG = {
    'default_start_date': '2022-01-01',
    'cache_data': True,
    'cache_dir': str(DATA_DIR),
    'retry_attempts': 3,
    'timeout': 30,
}

# Donnees (legacy support)
DATA_PATH = str(DATA_DIR)
MODELS_PATH = str(MODELS_DIR)
REPORTS_PATH = str(REPORTS_DIR)


# ============================================================================
# TICKERS
# ============================================================================
TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
DEFAULT_TICKERS = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']

BEAR_MARKET_SCENARIOS = {
    '2008_crisis': {
        'ticker': 'SPY',
        'start_date': '2007-10-01',
        'end_date': '2009-03-01',
        'name': '2008 Financial Crisis'
    },
    '2020_covid': {
        'ticker': 'SPY',
        'start_date': '2020-02-15',
        'end_date': '2020-04-15',
        'name': '2020 COVID Crash'
    },
    '2022_tech': {
        'ticker': 'QQQ',
        'start_date': '2022-01-01',
        'end_date': '2022-10-01',
        'name': '2022 Tech Selloff'
    },
}


# ============================================================================
# PERIODE DE DONNEES
# ============================================================================
START_DATE = '2022-01-01'
END_DATE = None  # None = aujourd'hui

# Periode de donnees (legacy)
PREDICTION_WINDOW = 5
PRICE_CHANGE_THRESHOLD = 0.01


# ============================================================================
# MODELE
# ============================================================================
MODEL_TYPE = 'gradient_boosting'
MODEL_CONFIG = {
    'default_model_type': 'gradient_boosting',
    'supported_models': ['gradient_boosting', 'random_forest', 'neural_network'],
    'train_test_split': 0.8,
    'scale_features': True,
    'feature_selection': True,
    
    # Gradient Boosting parameters
    'gb_params': {
        'n_estimators': 100,
        'learning_rate': 0.1,
        'max_depth': 5,
        'subsample': 0.8,
        'random_state': 42,
    },
    
    # Legacy params
    'GB_N_ESTIMATORS': 200,
    'GB_LEARNING_RATE': 0.05,
    'GB_MAX_DEPTH': 5,
    'GB_MIN_SAMPLES_SPLIT': 10,
    
    # Random Forest parameters
    'rf_params': {
        'n_estimators': 100,
        'max_depth': 10,
        'min_samples_split': 5,
        'random_state': 42,
    },
    
    # Legacy params
    'RF_N_ESTIMATORS': 200,
    'RF_MAX_DEPTH': 15,
    'RF_MIN_SAMPLES_SPLIT': 5,
}


# ============================================================================
# BACKTESTING CONFIG
# ============================================================================
INITIAL_CAPITAL = 10000
POSITION_SIZE_PCT = 0.95
BACKTEST_CONFIG = {
    'initial_capital': 10000,
    'position_size_pct': 0.95,
    'stop_loss_pct': -2.0,
    'take_profit_pct': 5.0,
    'use_trend_filter': True,
}


# ============================================================================
# STRATEGIE ADAPTATIVE (parametres par defaut)
# ============================================================================
STRATEGY_CONFIG = {
    'BULL': {
        'stop_loss_pct': -3.0,
        'take_profit_pct': 7.0,
        'use_trend_filter': False,
        'signal_threshold': 0.40,
        'mode': 'AGGRESSIVE',
        'description': 'Mode agressif: maximiser les gains'
    },
    'BEAR': {
        'stop_loss_pct': -1.0,
        'take_profit_pct': 2.0,
        'use_trend_filter': True,
        'signal_threshold': 0.60,
        'mode': 'DEFENSIVE',
        'description': 'Mode defensif: proteger le capital'
    },
    'SIDEWAYS': {
        'stop_loss_pct': -1.5,
        'take_profit_pct': 3.0,
        'use_trend_filter': True,
        'signal_threshold': 0.50,
        'mode': 'NEUTRAL',
        'description': 'Mode neutre: trading court terme'
    },
    'CONSOLIDATION': {
        'stop_loss_pct': -2.0,
        'take_profit_pct': 4.0,
        'use_trend_filter': True,
        'signal_threshold': 0.55,
        'mode': 'CAUTIOUS',
        'description': 'Mode prudent: attendre le breakout'
    },
    'UNKNOWN': {
        'stop_loss_pct': -2.0,
        'take_profit_pct': 5.0,
        'use_trend_filter': True,
        'signal_threshold': 0.50,
        'mode': 'STANDARD',
        'description': 'Mode standard: donnees insuffisantes'
    }
}


# ============================================================================
# FEATURE ENGINEERING
# ============================================================================
FEATURE_CONFIG = {
    'sma_periods': [20, 50, 100, 200],
    'ema_periods': [12, 26],
    'rsi_period': 14,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    'atr_period': 14,
    'bb_period': 20,
    'bb_std_dev': 2,
    'adx_period': 14,
}


# ============================================================================
# REGIME DETECTION
# ============================================================================
REGIME_CONFIG = {
    'sma_short': 20,
    'sma_long': 50,
    'sma_very_long': 200,
    'rsi_thresholds': {
        'oversold': 30,
        'overbought': 70,
    },
    'volatility_thresholds': {
        'low': 0.15,
        'high': 0.40,
    },
    'regime_confidence_thresholds': {
        'high': 0.70,
        'medium': 0.50,
        'low': 0.30,
    },
}


# ============================================================================
# LOGGING & REPORTING
# ============================================================================
VERBOSE = True
SHOW_PLOTS = True
SAVE_REPORTS = True

LOGGING_CONFIG = {
    'log_level': 'INFO',
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'save_to_file': True,
    'log_dir': str(LOG_DIR),
}

REPORTING_CONFIG = {
    'save_backtest_report': True,
    'save_html_report': False,
    'save_plots': True,
    'report_dir': str(REPORTS_DIR),
}

# Legacy
TEST_SIZE = 0.2
