"""
Continuous Trainer - Entrainement continu avec feedback adaptatif
Lance le pipeline complet chaque soir apres la cloture des marches US,
suit les performances cumulees et ajuste les parametres automatiquement.

Usage:
    python3 scripts/continuous_trainer.py                  # Lance la boucle continue
    python3 scripts/continuous_trainer.py --run-once       # Un seul cycle puis quitte
    python3 scripts/continuous_trainer.py --force-now      # Lance immediatement sans attendre l'heure
"""
import sys
import os
import json
import time
import signal
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
import schedule

# Setup paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src' / 'core'))
sys.path.insert(0, str(project_root / 'src' / 'strategies'))
sys.path.insert(0, str(project_root / 'scripts'))  # pour PerformanceTracker

from performance_tracker import PerformanceTracker
from config import DEFAULT_TICKERS, LOG_DIR, MODELS_DIR

# ============================================================================
# CONFIGURATION DU TRAINER
# ============================================================================
TRAINER_CONFIG = {
    # Heure de lancement du retrain (22h UTC = ~18h EST, apres cloture)
    'retrain_time_utc': '22:00',

    # Tickers a entrainer
    'tickers': DEFAULT_TICKERS,

    # Fichier d'etat persistant
    'state_file': str(project_root / 'data' / 'trainer_state.json'),

    # Seuils d'adaptation automatique
    'adaptation': {
        # Si win_rate < ce seuil sur les 5 derniers cycles -> rehausser le signal_threshold de +0.05
        'min_win_rate': 0.45,
        # Si return_pct < ce seuil sur les 3 derniers cycles -> serrer le stop_loss de 0.5%
        'min_return_pct': -1.0,
        # Si return_pct > ce seuil sur les 3 derniers cycles -> assouplir les params
        'good_return_pct': 5.0,
        # Nombre de cycles de memoire pour l'adaptation
        'lookback_cycles': 5,
    }
}


# ============================================================================
# SETUP LOGGING
# ============================================================================
def setup_trainer_logger():
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(exist_ok=True, parents=True)
    log_file = log_dir / f'trainer_{datetime.now().strftime("%Y%m")}.log'

    logger = logging.getLogger('continuous_trainer')
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Console
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(ch)

        # Fichier
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(fh)

    return logger


# ============================================================================
# GESTION DE L'ETAT PERSISTANT
# ============================================================================
def load_state(state_file: str) -> dict:
    """Charge l'etat du trainer (cycles passes, params ajustes)"""
    if Path(state_file).exists():
        with open(state_file, 'r') as f:
            return json.load(f)
    return {
        'total_cycles': 0,
        'last_run': None,
        'ticker_overrides': {},   # { 'TSLA': { 'signal_threshold': 0.35 } }
        'ticker_history': {},     # { 'AAPL': [{ cycle, return_pct, win_rate, ... }] }
    }


def save_state(state: dict, state_file: str):
    """Sauvegarde l'etat du trainer"""
    Path(state_file).parent.mkdir(exist_ok=True, parents=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2, default=str)


# ============================================================================
# ADAPTATION AUTOMATIQUE DES PARAMETRES
# ============================================================================
def adapt_ticker_params(ticker: str, state: dict, logger) -> dict:
    """
    Analyse l'historique de performance d'un ticker et ajuste les parametres.
    Retourne un dict d'overrides { 'signal_threshold': ..., 'stop_loss_pct': ... }
    """
    cfg = TRAINER_CONFIG['adaptation']
    history = state['ticker_history'].get(ticker, [])
    overrides = state['ticker_overrides'].get(ticker, {})

    if len(history) < 2:
        return overrides  # Pas assez de donnees

    recent = history[-cfg['lookback_cycles']:]
    avg_return = sum(c['return_pct'] for c in recent) / len(recent)
    avg_win_rate = sum(c['win_rate'] for c in recent) / len(recent)
    n_trades_total = sum(c['n_trades'] for c in recent)

    logger.info(f"  [{ticker}] Historique {len(recent)} cycles: "
                f"return_moy={avg_return:.2f}% | win_rate_moy={avg_win_rate:.1%} | "
                f"trades_total={n_trades_total}")

    changed = False

    # --- Trop de pertes : rehausser le seuil de signal ---
    if avg_win_rate < cfg['min_win_rate'] and n_trades_total >= 3:
        current = overrides.get('signal_threshold', 0.45)
        new_val = min(0.65, round(current + 0.03, 3))
        if new_val != current:
            overrides['signal_threshold'] = new_val
            logger.info(f"  [{ticker}] ADAPTATION: win_rate faible ({avg_win_rate:.1%}) "
                        f"-> signal_threshold {current} -> {new_val}")
            changed = True

    # --- Rendement negatif persistant : serrer le stop loss ---
    if avg_return < cfg['min_return_pct'] and len(recent) >= 3:
        current_sl = overrides.get('stop_loss_pct', -2.0)
        new_sl = max(-1.0, round(current_sl + 0.5, 1))   # moins negatif = plus serré
        if new_sl != current_sl:
            overrides['stop_loss_pct'] = new_sl
            logger.info(f"  [{ticker}] ADAPTATION: rendement negatif ({avg_return:.2f}%) "
                        f"-> stop_loss {current_sl}% -> {new_sl}%")
            changed = True

    # --- Bonne performance : assouplir progressivement ---
    if avg_return > cfg['good_return_pct'] and avg_win_rate > 0.65:
        current = overrides.get('signal_threshold', 0.45)
        new_val = max(0.35, round(current - 0.02, 3))
        if new_val != current:
            overrides['signal_threshold'] = new_val
            logger.info(f"  [{ticker}] ADAPTATION: excellente perf ({avg_return:.2f}%) "
                        f"-> signal_threshold assoupli {current} -> {new_val}")
            changed = True

    if not changed:
        logger.info(f"  [{ticker}] Pas d'adaptation necessaire")

    state['ticker_overrides'][ticker] = overrides
    return overrides


# ============================================================================
# CYCLE DE TRAINING
# ============================================================================
def run_training_cycle(logger, run_once=False):
    """Lance un cycle complet de training pour tous les tickers"""

    # Import ici pour eviter les imports circulaires au demarrage
    from production_main import ProductionTradingPipeline
    from config import START_DATE

    state_file = TRAINER_CONFIG['state_file']
    state = load_state(state_file)

    cycle_num = state['total_cycles'] + 1
    cycle_start = datetime.now()

    logger.info("=" * 70)
    logger.info(f"CYCLE #{cycle_num} - {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)

    # Analyse des performances passees et adaptation
    logger.info("--- PHASE 1: ANALYSE & ADAPTATION ---")
    for ticker in TRAINER_CONFIG['tickers']:
        adapt_ticker_params(ticker, state, logger)

    # Tracker de performance pour ce cycle
    tracker = PerformanceTracker(project_root / 'data' / 'performance_history.json')

    cycle_results = {}

    # Lancement du pipeline pour chaque ticker
    logger.info("--- PHASE 2: TRAINING & BACKTEST ---")
    for ticker in TRAINER_CONFIG['tickers']:
        logger.info(f"\n>>> Ticker: {ticker}")
        try:
            overrides = state['ticker_overrides'].get(ticker, {})

            pipeline = ProductionTradingPipeline(
                ticker=ticker,
                config=overrides,
                use_optimized_params=False
            )

            # Injecter les overrides dans run_backtest via la config
            pipeline._signal_threshold_override = overrides.get('signal_threshold', None)
            pipeline._stop_loss_override = overrides.get('stop_loss_pct', None)

            success = pipeline.run_complete_pipeline(start_date=START_DATE)

            if success and pipeline.backtest_results:
                r = pipeline.backtest_results
                result = {
                    'cycle': cycle_num,
                    'date': cycle_start.isoformat(),
                    'return_pct': r.get('total_return_pct', 0),
                    'win_rate': r.get('win_rate', 0) / 100,
                    'n_trades': r.get('buy_trades', 0),
                    'max_drawdown': r.get('max_drawdown', 0),
                    'final_value': r.get('final_value', 10000),
                    'overrides_used': overrides,
                }
                cycle_results[ticker] = result

                # Ajouter a l'historique du ticker
                if ticker not in state['ticker_history']:
                    state['ticker_history'][ticker] = []
                state['ticker_history'][ticker].append(result)

                # Enregistrer dans le tracker global
                tracker.record(ticker, result)

                logger.info(f"  [{ticker}] Cycle #{cycle_num}: "
                            f"return={result['return_pct']:.2f}% | "
                            f"win_rate={result['win_rate']:.1%} | "
                            f"trades={result['n_trades']}")
            else:
                logger.warning(f"  [{ticker}] Pipeline echoue ou sans resultats")

        except Exception as e:
            logger.error(f"  [{ticker}] ERREUR: {e}", exc_info=True)

    # Resume du cycle
    logger.info("\n--- PHASE 3: RESUME DU CYCLE ---")
    if cycle_results:
        total_returns = [v['return_pct'] for v in cycle_results.values()]
        avg_return = sum(total_returns) / len(total_returns)
        logger.info(f"Tickers traites: {list(cycle_results.keys())}")
        logger.info(f"Rendement moyen: {avg_return:.2f}%")
        for t, r in cycle_results.items():
            status = "OK" if r['return_pct'] >= 0 else "WARN"
            logger.info(f"  [{status}] {t}: {r['return_pct']:+.2f}% | WR={r['win_rate']:.1%} | "
                        f"Trades={r['n_trades']}")

        # Afficher le leaderboard global
        tracker.print_summary(logger)

    # Sauvegarder l'etat
    state['total_cycles'] = cycle_num
    state['last_run'] = cycle_start.isoformat()
    save_state(state, state_file)

    elapsed = (datetime.now() - cycle_start).total_seconds()
    logger.info(f"\nCycle #{cycle_num} termine en {elapsed:.0f}s")
    logger.info(f"Prochain cycle dans ~1 minute")
    logger.info("=" * 70)


# ============================================================================
# BOUCLE PRINCIPALE
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description='Continuous Trainer - Algo Trading')
    parser.add_argument('--run-once', action='store_true',
                        help='Lance un seul cycle puis quitte')
    parser.add_argument('--force-now', action='store_true',
                        help='Lance immediatement sans attendre l\'heure schedulee')
    args = parser.parse_args()

    logger = setup_trainer_logger()

    try:
        _main_loop(args, logger)
    except Exception as e:
        logger.critical(f"ERREUR FATALE: {e}", exc_info=True)
        sys.exit(1)


def _main_loop(args, logger):

    # Gestion du signal d'arret propre (Ctrl+C ou SIGTERM)
    shutdown = {'requested': False}

    def handle_shutdown(signum, frame):
        logger.info("Signal d'arret recu - arret propre en cours...")
        shutdown['requested'] = True

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    logger.info("=" * 70)
    logger.info("CONTINUOUS TRAINER DEMARRE")
    logger.info(f"Tickers: {TRAINER_CONFIG['tickers']}")
    logger.info(f"Heure de retrain: {TRAINER_CONFIG['retrain_time_utc']} UTC chaque jour")
    logger.info("=" * 70)

    if args.run_once or args.force_now:
        # Mode immediat
        logger.info("Mode: execution immediate unique")
        run_training_cycle(logger, run_once=True)
        return

    # Mode continu: schedule le retrain toutes les minutes
    schedule.every(1).minutes.do(run_training_cycle, logger=logger)

    logger.info("Scheduler actif. Cycle toutes les 1 minute(s)")
    logger.info("Appuyez sur Ctrl+C pour arreter proprement")

    while not shutdown['requested']:
        schedule.run_pending()
        time.sleep(30)  # Verifie toutes les 30 secondes

    logger.info("Continuous Trainer arrete proprement.")


if __name__ == '__main__':
    main()
