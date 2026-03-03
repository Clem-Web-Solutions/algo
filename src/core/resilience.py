"""
Module de résilience - mitigations pour pannes réseau/infrastructure, volatilité extrême,
et défaillances API.

Composants:
  - retry_with_backoff   : décorateur retry exponentiel (scénarios 1, 7)
  - RateLimiter          : singleton thread-safe inter-appels yfinance (scénario 7)
  - CircuitBreaker       : disjoncteur vol extrême + erreurs consécutives (scénario 4)
  - PositionStateManager : persistance JSON des positions ouvertes (scénarios 2, 3)
  - IBConnectionManager  : stub reconnexion TWS (scénario 2)
  - OrderRejectionHandler: stub gestion rejets IB (scénario 6)
"""
import json
import logging
import random
import threading
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# RETRY WITH BACKOFF (scénarios 1, 7)
# ============================================================================

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 120.0,
    exceptions: tuple = (Exception,),
):
    """
    Décorateur retry avec backoff exponentiel et jitter.

    delay_n = min(base_delay * 2^attempt + jitter, max_delay)

    Args:
        max_retries: Nombre maximum de tentatives (après le premier essai)
        base_delay : Délai de base en secondes
        max_delay  : Plafond du délai en secondes
        exceptions : Types d'exceptions à intercepter
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exc: Optional[Exception] = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == max_retries:
                        break
                    delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                    logger.warning(
                        f"[Retry] {func.__name__} échoué (tentative {attempt + 1}/{max_retries}): "
                        f"{exc}. Nouvel essai dans {delay:.1f}s"
                    )
                    time.sleep(delay)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


# ============================================================================
# RATE LIMITER (scénario 7)
# ============================================================================

class RateLimiter:
    """
    Singleton thread-safe pour limiter la fréquence des appels API (yfinance).

    Usage:
        rate_limiter = RateLimiter.get_instance()
        rate_limiter.wait()
        data = yf.download(...)
    """
    _instance: Optional['RateLimiter'] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self, min_interval_s: float = 0.5):
        self._min_interval = min_interval_s
        self._last_call: float = 0.0
        self._call_lock = threading.Lock()

    @classmethod
    def get_instance(cls, min_interval_s: float = 0.5) -> 'RateLimiter':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(min_interval_s)
        return cls._instance

    def wait(self) -> None:
        """Attend si nécessaire pour respecter l'intervalle minimum entre appels."""
        with self._call_lock:
            now = time.monotonic()
            elapsed = now - self._last_call
            if elapsed < self._min_interval:
                time.sleep(self._min_interval - elapsed)
            self._last_call = time.monotonic()


# Module-level singleton pour import direct
_yfinance_limiter = RateLimiter.get_instance(min_interval_s=0.5)


def yfinance_rate_limit() -> None:
    """Appeler avant chaque yf.download() pour respecter le pacing yfinance."""
    _yfinance_limiter.wait()


# ============================================================================
# CIRCUIT BREAKER (scénario 4)
# ============================================================================

class CircuitBreaker:
    """
    Disjoncteur pour bloquer les trades lors de conditions extrêmes.

    États: CLOSED (normal) → OPEN (bloqué) → HALF_OPEN (test) → CLOSED

    Conditions de déclenchement:
      - Volatilité annualisée > vol_threshold (défaut 80%)
      - Perte journalière > daily_loss_limit (défaut -5%)
      - N erreurs consécutives > max_errors (défaut 3)

    Récupération automatique après recovery_period_s (défaut 3600s = 1h).
    """

    CLOSED = 'CLOSED'
    OPEN = 'OPEN'
    HALF_OPEN = 'HALF_OPEN'

    def __init__(
        self,
        vol_threshold: float = 0.80,
        daily_loss_limit: float = -0.05,
        max_errors: int = 3,
        recovery_period_s: float = 3600.0,
    ):
        self.vol_threshold = vol_threshold
        self.daily_loss_limit = daily_loss_limit
        self.max_errors = max_errors
        self.recovery_period_s = recovery_period_s

        self._state = self.CLOSED
        self._trip_reason: str = ''
        self._opened_at: Optional[float] = None
        self._consecutive_errors: int = 0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # État public
    # ------------------------------------------------------------------

    @property
    def state(self) -> str:
        self._check_recovery()
        return self._state

    def is_trading_allowed(self) -> bool:
        """Retourne True si les trades sont autorisés (circuit fermé ou semi-ouvert)."""
        return self.state != self.OPEN

    def get_status(self) -> dict:
        return {
            'state': self.state,
            'trip_reason': self._trip_reason,
            'consecutive_errors': self._consecutive_errors,
            'opened_at': datetime.fromtimestamp(self._opened_at).isoformat() if self._opened_at else None,
        }

    # ------------------------------------------------------------------
    # Déclencheurs
    # ------------------------------------------------------------------

    def check_volatility(self, annualized_vol: float) -> bool:
        """
        Vérifie la volatilité. Trip si > seuil.
        Retourne True si le circuit a été déclenché.
        """
        if annualized_vol >= self.vol_threshold:
            self._trip(f"Volatilité extrême: {annualized_vol:.1%} >= {self.vol_threshold:.1%}")
            return True
        return False

    def check_daily_loss(self, daily_return: float) -> bool:
        """
        Vérifie la perte journalière. Trip si < limite.
        Retourne True si le circuit a été déclenché.
        """
        if daily_return <= self.daily_loss_limit:
            self._trip(f"Perte journalière excessive: {daily_return:.1%} <= {self.daily_loss_limit:.1%}")
            return True
        return False

    def record_error(self) -> bool:
        """
        Enregistre une erreur consécutive. Trip si > max_errors.
        Retourne True si le circuit a été déclenché.
        """
        with self._lock:
            self._consecutive_errors += 1
            if self._consecutive_errors >= self.max_errors:
                self._trip(f"{self._consecutive_errors} erreurs consécutives")
                return True
        return False

    def record_success(self) -> None:
        """Réinitialise le compteur d'erreurs après un succès."""
        with self._lock:
            self._consecutive_errors = 0
            if self._state == self.HALF_OPEN:
                self._state = self.CLOSED
                self._trip_reason = ''
                logger.info("[CircuitBreaker] Circuit FERMÉ (succès en HALF_OPEN)")

    def reset(self) -> None:
        """Réinitialise manuellement le circuit."""
        with self._lock:
            self._state = self.CLOSED
            self._trip_reason = ''
            self._opened_at = None
            self._consecutive_errors = 0
            logger.info("[CircuitBreaker] Circuit réinitialisé manuellement")

    # ------------------------------------------------------------------
    # Privé
    # ------------------------------------------------------------------

    def _trip(self, reason: str) -> None:
        with self._lock:
            if self._state != self.OPEN:
                self._state = self.OPEN
                self._trip_reason = reason
                self._opened_at = time.monotonic()
                logger.warning(f"[CircuitBreaker] OUVERT: {reason}")

    def _check_recovery(self) -> None:
        with self._lock:
            if self._state == self.OPEN and self._opened_at is not None:
                elapsed = time.monotonic() - self._opened_at
                if elapsed >= self.recovery_period_s:
                    self._state = self.HALF_OPEN
                    logger.info(
                        f"[CircuitBreaker] HALF_OPEN après {elapsed:.0f}s — "
                        "prochain succès fermera le circuit"
                    )


# ============================================================================
# POSITION STATE MANAGER (scénarios 2, 3)
# ============================================================================

class PositionStateManager:
    """
    Persistance JSON des positions ouvertes pour la détection post-crash.

    Fichier: data/position_state.json
    Format:
        {
          "positions": {
            "AAPL": {
              "entry_price": 180.5,
              "quantity": 55.2,
              "entry_date": "2026-03-02",
              "reason": "Buy Signal",
              "saved_at": "2026-03-02T22:01:00"
            }
          },
          "last_updated": "2026-03-02T22:01:00"
        }
    """

    def __init__(self, state_file: str, orphan_hours: float = 24.0):
        self._path = Path(state_file)
        self._orphan_hours = orphan_hours
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    # ------------------------------------------------------------------
    # API publique
    # ------------------------------------------------------------------

    def save_position(
        self,
        ticker: str,
        entry_price: float,
        quantity: float,
        entry_date: str,
        reason: str = '',
    ) -> None:
        """Enregistre une position ouverte (appeler après _execute_buy)."""
        self._state['positions'][ticker] = {
            'entry_price': entry_price,
            'quantity': quantity,
            'entry_date': entry_date,
            'reason': reason,
            'saved_at': datetime.now().isoformat(),
        }
        self._persist()

    def clear_position(self, ticker: str) -> None:
        """Supprime une position fermée (appeler après _execute_sell)."""
        if ticker in self._state['positions']:
            del self._state['positions'][ticker]
            self._persist()

    def get_all_positions(self) -> dict:
        """Retourne toutes les positions persistées."""
        return dict(self._state['positions'])

    def has_orphan_positions(self) -> bool:
        """
        Retourne True si des positions ont été sauvegardées il y a plus de
        `orphan_hours` heures sans mise à jour (signe d'un crash précédent).
        """
        last_updated_str = self._state.get('last_updated')
        if not last_updated_str or not self._state['positions']:
            return False
        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            age = datetime.now() - last_updated
            return age > timedelta(hours=self._orphan_hours)
        except (ValueError, TypeError):
            return False

    def clear_all(self) -> None:
        """Vide toutes les positions (ex: après récupération manuelle confirmée)."""
        self._state['positions'] = {}
        self._persist()

    # ------------------------------------------------------------------
    # Privé
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        if self._path.exists():
            try:
                with open(self._path) as f:
                    data = json.load(f)
                    if 'positions' not in data:
                        data['positions'] = {}
                    return data
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(f"[PositionStateManager] Fichier corrompu, réinitialisé: {exc}")
        return {'positions': {}, 'last_updated': None}

    def _persist(self) -> None:
        self._state['last_updated'] = datetime.now().isoformat()
        try:
            with open(self._path, 'w') as f:
                json.dump(self._state, f, indent=2)
        except OSError as exc:
            logger.error(f"[PositionStateManager] Impossible d'écrire {self._path}: {exc}")


# ============================================================================
# STUBS IB (scénarios 2, 6)
# ============================================================================

class IBConnectionManager:
    """
    Stub pour la gestion de la connexion TWS/IB Gateway.

    Ce composant est un framework extensible — l'intégration IB live
    n'étant pas encore active, les méthodes journalisent l'intention
    et retournent des valeurs sûres par défaut.

    Pour activer: implémenter avec ib_insync ou ibapi.
    """

    def __init__(self, host: str = '127.0.0.1', port: int = 7497, client_id: int = 1):
        self.host = host
        self.port = port
        self.client_id = client_id
        self._connected = False

    def connect(self) -> bool:
        """Tente une connexion à TWS. STUB — retourne False (non implémenté)."""
        logger.info(f"[IBConnectionManager] STUB connect({self.host}:{self.port}) — non implémenté")
        return False

    def disconnect(self) -> None:
        """Déconnecte proprement. STUB."""
        logger.info("[IBConnectionManager] STUB disconnect() — non implémenté")
        self._connected = False

    def reconnect(self, max_attempts: int = 3, delay_s: float = 5.0) -> bool:
        """
        Tente une reconnexion avec retry. STUB.

        Pour implémenter: boucle avec ib.connect() + backoff + vérification état.
        """
        logger.warning(
            f"[IBConnectionManager] STUB reconnect() appelé (max={max_attempts}) — "
            "TWS non connecté. Implémenter avec ib_insync."
        )
        return False

    def is_connected(self) -> bool:
        """Retourne l'état de connexion. STUB — toujours False."""
        return self._connected

    def get_open_positions(self) -> list:
        """Récupère les positions ouvertes depuis IB. STUB — retourne liste vide."""
        logger.info("[IBConnectionManager] STUB get_open_positions() — retourne []")
        return []


class OrderRejectionHandler:
    """
    Stub pour la gestion des rejets d'ordres IB.

    Catégories de rejet gérées (framework):
      - 'INSUFFICIENT_FUNDS'  → réduire taille position
      - 'OUTSIDE_RTH'         → attendre l'ouverture marché
      - 'INVALID_PRICE'       → recalculer prix limite
      - 'UNKNOWN'             → logger + alerter

    Pour activer: connecter à ibapi.EWrapper.orderStatus / error callbacks.
    """

    RETRY_REASONS = {'INVALID_PRICE', 'TEMPORARY_ERROR'}
    NO_RETRY_REASONS = {'INSUFFICIENT_FUNDS', 'OUTSIDE_RTH', 'ACCOUNT_RESTRICTED'}

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries
        self._rejection_log: list = []

    def handle_rejection(self, reason: str, order: dict) -> dict:
        """
        Traite un rejet d'ordre.

        Args:
            reason: Code du rejet IB (ex: 'INSUFFICIENT_FUNDS')
            order : Dict décrivant l'ordre rejeté {'ticker', 'action', 'qty', 'price'}

        Returns:
            Dict avec {'action': 'retry'|'cancel'|'reduce', 'modified_order': ...}
        """
        event = {
            'timestamp': datetime.now().isoformat(),
            'reason': reason,
            'order': order,
        }
        self._rejection_log.append(event)

        ticker = order.get('ticker', '?')
        logger.warning(f"[OrderRejectionHandler] Rejet ordre {ticker}: {reason}")

        if reason in self.NO_RETRY_REASONS:
            logger.error(f"[OrderRejectionHandler] Rejet définitif ({reason}) — ordre annulé")
            return {'action': 'cancel', 'modified_order': None}

        if reason == 'INSUFFICIENT_FUNDS':
            reduced_qty = order.get('qty', 0) * 0.5
            logger.info(f"[OrderRejectionHandler] Réduction quantité: {order.get('qty')} -> {reduced_qty:.2f}")
            modified = {**order, 'qty': reduced_qty}
            return {'action': 'reduce', 'modified_order': modified}

        if reason in self.RETRY_REASONS:
            return {'action': 'retry', 'modified_order': order}

        # Cas inconnu: logger et annuler
        logger.error(f"[OrderRejectionHandler] Raison inconnue '{reason}' — ordre annulé par précaution")
        return {'action': 'cancel', 'modified_order': None}

    def get_rejection_log(self) -> list:
        return list(self._rejection_log)
