"""
ML Optimizer — Métriques financières et optimisation du pipeline de trading.

Remplace les métriques statistiques (F1, AUC) par des métriques directement liées
à la profitabilité réelle: Sharpe ratio, profit factor, expectancy.

Fonctions principales:
  compute_financial_metrics    — Sharpe, profit factor, expectancy depuis prédictions
  optimize_signal_threshold    — Seuil optimal maximisant le Sharpe (sur validation uniquement)
  fractional_kelly             — Sizing dynamique sécurisé (quarter-Kelly)
  walk_forward_financial_eval  — CV walk-forward avec métriques financières

IMPORTANT: optimize_signal_threshold doit être appelé UNIQUEMENT sur des données
de validation (jamais sur X_test) pour éviter le sur-ajustement du seuil.
"""
import logging
import numpy as np
import pandas as pd
from typing import Optional

logger = logging.getLogger(__name__)


# ============================================================================
# MÉTRIQUES FINANCIÈRES
# ============================================================================

def compute_financial_metrics(
    predictions: np.ndarray,
    forward_returns_pct: np.ndarray,
    commission_pct: float = 0.1,
    slippage_pct: float = 0.05,
) -> dict:
    """
    Calcule les métriques financières depuis des prédictions binaires.

    Logique: si prediction=1 (BUY) → on entre et sort 5j plus tard.
    Retour net = forward_return - commission_aller - commission_retour
                               - slippage_aller   - slippage_retour

    Args:
        predictions        : Array 0/1 (1=BUY)
        forward_returns_pct: Retours réels à l'horizon N jours en % (même longueur que predictions)
        commission_pct     : Commission aller+retour en % (défaut 0.1% × 2 = 0.2%)
        slippage_pct       : Slippage aller+retour en %  (défaut 0.05% × 2 = 0.1%)

    Returns:
        Dict: sharpe, profit_factor, expectancy, win_rate, n_trades,
              avg_win_pct, avg_loss_pct, max_drawdown_pct
    """
    total_cost_pct = commission_pct * 2 + slippage_pct * 2

    buy_mask = predictions == 1
    n_trades = int(buy_mask.sum())

    empty = {
        'sharpe': 0.0, 'profit_factor': 0.0, 'expectancy': 0.0,
        'win_rate': 0.0, 'n_trades': 0, 'avg_win_pct': 0.0,
        'avg_loss_pct': 0.0, 'max_drawdown_pct': 0.0,
    }
    if n_trades == 0:
        return empty

    trade_returns = forward_returns_pct[buy_mask] - total_cost_pct

    # Série P&L quotidienne (jours sans trade = 0 → cash)
    daily_pnl = np.zeros(len(predictions))
    daily_pnl[buy_mask] = trade_returns

    # Sharpe annualisé (base 252 jours de trading)
    mean_r = np.mean(daily_pnl)
    std_r = np.std(daily_pnl) + 1e-9
    sharpe = float((mean_r / std_r) * np.sqrt(252))

    # Win rate & profit factor
    wins = trade_returns[trade_returns > 0]
    losses = trade_returns[trade_returns <= 0]
    win_rate = len(wins) / n_trades
    gross_profit = float(wins.sum()) if len(wins) > 0 else 0.0
    gross_loss = float(abs(losses.sum())) if len(losses) > 0 else 1e-9
    profit_factor = gross_profit / gross_loss

    # Expectancy (retour moyen net par trade en %)
    expectancy = float(trade_returns.mean())

    # Drawdown maximal (cumulatif)
    cumulative = np.cumsum(daily_pnl)
    running_max = np.maximum.accumulate(cumulative)
    max_drawdown_pct = float(np.min(cumulative - running_max))

    return {
        'sharpe': round(sharpe, 4),
        'profit_factor': round(profit_factor, 4),
        'expectancy': round(expectancy, 4),
        'win_rate': round(win_rate, 4),
        'n_trades': n_trades,
        'avg_win_pct': round(float(wins.mean()) if len(wins) > 0 else 0.0, 4),
        'avg_loss_pct': round(float(losses.mean()) if len(losses) > 0 else 0.0, 4),
        'max_drawdown_pct': round(max_drawdown_pct, 4),
    }


# ============================================================================
# OPTIMISATION DU SEUIL DE SIGNAL
# ============================================================================

def optimize_signal_threshold(
    probas: np.ndarray,
    forward_returns_pct: np.ndarray,
    thresholds: Optional[np.ndarray] = None,
    commission_pct: float = 0.1,
    slippage_pct: float = 0.05,
    min_trades: int = 5,
) -> tuple:
    """
    Cherche le seuil de probabilité maximisant le Sharpe ratio.

    À appeler UNIQUEMENT sur des données de VALIDATION — jamais sur X_test.
    Le seuil optimal est ensuite appliqué sur le jeu de test.

    Args:
        probas              : Probabilités P(classe=1) sur la validation
        forward_returns_pct : Retours à N jours en % correspondants
        thresholds          : Grille testée (défaut: 0.30 → 0.70 par pas 0.02)
        commission_pct      : Commission aller+retour en %
        slippage_pct        : Slippage aller+retour en %
        min_trades          : Nombre minimum de trades pour valider un seuil

    Returns:
        (optimal_threshold: float, metrics_df: pd.DataFrame)
        metrics_df classé par Sharpe décroissant — utile pour diagnostics
    """
    if thresholds is None:
        thresholds = np.arange(0.45, 0.72, 0.02)  # min 0.45 : évite les seuils trop bas (sur-optimisation)

    results = []
    for thr in thresholds:
        preds = (probas >= thr).astype(int)
        m = compute_financial_metrics(preds, forward_returns_pct, commission_pct, slippage_pct)
        if m['n_trades'] >= min_trades:
            results.append({'threshold': round(float(thr), 3), **m})

    if not results:
        logger.warning("[MLOptimizer] Aucun seuil valide (trop peu de trades) — fallback 0.50")
        return 0.50, pd.DataFrame()

    df = pd.DataFrame(results).sort_values('sharpe', ascending=False)
    best_thr = float(df.iloc[0]['threshold'])

    logger.info(
        f"[MLOptimizer] Seuil optimal: {best_thr:.2f} | "
        f"Sharpe={df.iloc[0]['sharpe']:.3f} | "
        f"PF={df.iloc[0]['profit_factor']:.3f} | "
        f"Trades={df.iloc[0]['n_trades']}"
    )
    return best_thr, df


# ============================================================================
# FRACTIONAL KELLY
# ============================================================================

def fractional_kelly(
    win_rate: float,
    avg_win_pct: float,
    avg_loss_pct: float,
    fraction: float = 0.25,
    max_size_pct: float = 0.95,
    min_size_pct: float = 0.20,
) -> float:
    """
    Taille de position selon le critère de Kelly fractionnel (sécurisé).

    Formule Kelly:  f* = (p·b - q) / b   où b = avg_win / |avg_loss|
    Kelly fractionnel: f* × fraction   (défaut: quarter-Kelly = 25%)
    Clippé dans [min_size_pct, max_size_pct] pour la sécurité.

    Args:
        win_rate     : Taux de réussite observé sur la validation (0-1)
        avg_win_pct  : Retour moyen des trades gagnants en % (positif)
        avg_loss_pct : Retour moyen des trades perdants en % (négatif)
        fraction     : Fraction du Kelly à utiliser (0.25 = quarter-Kelly)
        max_size_pct : Plafond de position (clip sécurité)
        min_size_pct : Plancher de position

    Returns:
        position_size_pct ∈ [min_size_pct, max_size_pct]
    """
    if avg_loss_pct >= 0 or win_rate <= 0 or avg_win_pct <= 0:
        logger.warning("[Kelly] Données invalides → position minimale")
        return min_size_pct

    b = avg_win_pct / abs(avg_loss_pct)  # ratio gain/perte
    p = win_rate
    q = 1.0 - win_rate
    kelly_full = (p * b - q) / b

    if kelly_full <= 0:
        logger.warning(f"[Kelly] Edge négatif (f*={kelly_full:.3f}) → position minimale")
        return min_size_pct

    kelly_frac = kelly_full * fraction
    result = float(np.clip(kelly_frac, min_size_pct, max_size_pct))

    logger.info(
        f"[Kelly] b={b:.2f} | p={p:.1%} | f*={kelly_full:.3f} "
        f"× {fraction} = {kelly_frac:.3f} → sizing={result:.3f}"
    )
    return result


# ============================================================================
# WALK-FORWARD FINANCIAL EVALUATION
# ============================================================================

def walk_forward_financial_eval(
    model,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    close_prices: pd.Series,
    prediction_window: int = 5,
    n_splits: int = 5,
    commission_pct: float = 0.1,
    slippage_pct: float = 0.05,
) -> dict:
    """
    Évaluation walk-forward avec métriques financières (remplace F1 cross-val).

    Pour chaque fold TimeSeriesSplit:
      1. Entraîne un clone du modèle sur le fold train (avec sample_weight par fold)
      2. Prédit les probabilités sur le fold validation
      3. Calcule les métriques financières avec les vrais retours à N jours

    L'avantage vs cross_val_score(scoring='f1'):
      - Sample_weight correct (recalculé par fold, pas global)
      - Métriques alignées sur la profitabilité réelle
      - Détecte le sur-ajustement financier même si F1 est stable

    Args:
        model            : Modèle sklearn avec predict_proba
        X_train          : Features d'entraînement (index datetime)
        y_train          : Target binaire
        close_prices     : Série Close complète (doit couvrir X_train + prediction_window)
        prediction_window: Fenêtre de prédiction en jours
        n_splits         : Folds walk-forward
        commission_pct   : Commission aller+retour en %
        slippage_pct     : Slippage aller+retour en %

    Returns:
        Dict avec métriques moyennes ± std: sharpe_mean, profit_factor_mean, etc.
    """
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.base import clone
    from sklearn.utils.class_weight import compute_sample_weight
    from sklearn.metrics import f1_score as sk_f1

    tscv = TimeSeriesSplit(n_splits=n_splits)
    fold_metrics = []

    for fold_idx, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
        X_fold_tr = X_train.iloc[train_idx]
        X_fold_val = X_train.iloc[val_idx]
        y_fold_tr = y_train.iloc[train_idx]
        y_fold_val = y_train.iloc[val_idx]

        # Sample weights recalculés par fold — fix vs sample_weight global
        fold_model = clone(model)
        try:
            sw = compute_sample_weight('balanced', y_fold_tr)
            fold_model.fit(X_fold_tr, y_fold_tr, sample_weight=sw)
        except TypeError:
            fold_model.fit(X_fold_tr, y_fold_tr)

        # Probabilités sur la validation
        try:
            probas_val = fold_model.predict_proba(X_fold_val)[:, 1]
        except Exception:
            probas_val = fold_model.predict(X_fold_val).astype(float)
        preds_val = (probas_val >= 0.5).astype(int)

        # Retours forward pour les dates de validation
        fwd_returns = _compute_forward_returns(close_prices, X_fold_val.index, prediction_window)

        # Filtrer les NaN (dates trop proches de la fin)
        valid = ~np.isnan(fwd_returns)
        if valid.sum() < 3:
            continue

        fin_m = compute_financial_metrics(
            preds_val[valid], fwd_returns[valid], commission_pct, slippage_pct
        )
        f1 = sk_f1(y_fold_val.values[valid], preds_val[valid], zero_division=0)
        fold_metrics.append({**fin_m, 'f1': f1, 'fold': fold_idx + 1})

        logger.info(
            f"  Fold {fold_idx+1}/{n_splits}: "
            f"Sharpe={fin_m['sharpe']:+.3f} | "
            f"PF={fin_m['profit_factor']:.3f} | "
            f"Exp={fin_m['expectancy']:+.3f}% | "
            f"WR={fin_m['win_rate']:.1%} | "
            f"F1={f1:.3f}"
        )

    if not fold_metrics:
        return {}

    metrics_avg = {}
    for key in ['sharpe', 'profit_factor', 'expectancy', 'win_rate', 'f1',
                'n_trades', 'max_drawdown_pct']:
        values = [m[key] for m in fold_metrics if key in m]
        if values:
            metrics_avg[f'{key}_mean'] = round(float(np.mean(values)), 4)
            metrics_avg[f'{key}_std'] = round(float(np.std(values)), 4)

    return metrics_avg


# ============================================================================
# HELPER
# ============================================================================

def _compute_forward_returns(
    close_prices: pd.Series,
    dates,
    prediction_window: int,
) -> np.ndarray:
    """
    Calcule les retours à prediction_window jours pour chaque date.

    Args:
        close_prices    : Série Close avec index datetime
        dates           : Dates pour lesquelles calculer les retours
        prediction_window: Nombre de jours forward

    Returns:
        Array de retours en % (np.nan si impossible)
    """
    fwd_returns = []
    close_idx = close_prices.index

    for date in dates:
        if date not in close_idx:
            fwd_returns.append(np.nan)
            continue
        loc = close_idx.get_loc(date)
        if isinstance(loc, slice):
            loc = loc.start
        future_loc = loc + prediction_window
        if future_loc < len(close_prices):
            ret = (close_prices.iloc[future_loc] / close_prices.iloc[loc] - 1) * 100
            fwd_returns.append(float(ret))
        else:
            fwd_returns.append(np.nan)

    return np.array(fwd_returns)
