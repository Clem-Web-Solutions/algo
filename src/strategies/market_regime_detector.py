"""
Module de detection de regime de marche - Etape 8
Detecte si le marche est en: BULL, BEAR ou SIDEWAYS
Ameliore avec MACD, ADX et SMA adaptatif
"""
import pandas as pd
import numpy as np
from itertools import product


class MarketRegimeDetector:
    """Détecte le régime de marché en temps réel avec indicateurs avancés"""

    
    @staticmethod
    def detect_regime(data, sma_short=50, sma_long=200, lookback_days=60, use_adaptive_sma=True):
        """
        Detecte le regime de marche actuel avec indicateurs avances
        
        Args:
            data: DataFrame avec 'Close' et les SMAs
            sma_short: Periode SMA court terme (defaut: 50)
            sma_long: Periode SMA long terme (defaut: 200)
            lookback_days: Nombre de jours pour calculer la pente
            use_adaptive_sma: Utiliser SMA adaptatif base sur volatilite
        
        Returns:
            Dictionnaire avec regime et caracteristiques
        """
        if len(data) < max(sma_long, lookback_days):
            return {
                'regime': 'UNKNOWN',
                'confidence': 0.0,
                'trend_strength': 0.0,
                'slope': 0.0,
                'volatility': 0.0,
                'macd_signal': 0.0,
                'adx_signal': 0.0
            }
        
        # SMA adaptatif basé sur volatilité
        if use_adaptive_sma:
            sma_short, sma_long = MarketRegimeDetector._get_adaptive_sma_periods(data)
        
        latest = data.iloc[-1]
        current_price = float(latest['Close'].values[0] if hasattr(latest['Close'], 'values') else latest['Close'])
        
        # Créer les SMAs si elles n'existent pas
        if f'SMA_{sma_short}' not in data.columns:
            data[f'SMA_{sma_short}'] = data['Close'].rolling(window=sma_short).mean()
        if f'SMA_{sma_long}' not in data.columns:
            data[f'SMA_{sma_long}'] = data['Close'].rolling(window=sma_long).mean()
        
        sma_short_val = float(data[f'SMA_{sma_short}'].iloc[-1])
        sma_long_val = float(data[f'SMA_{sma_long}'].iloc[-1])
        
        # Calculer la pente (momentum)
        recent_data = data['Close'].iloc[-lookback_days:].values.astype(float)
        x = np.arange(len(recent_data))
        z = np.polyfit(x, recent_data, 1)
        slope = z[0].item() if hasattr(z[0], 'item') else float(z[0])
        
        # Normaliser la pente
        avg_price = float(np.mean(recent_data))
        slope_pct = float((slope / avg_price) * 100 if avg_price != 0 else 0)
        
        # Calculer la volatilité
        returns = data['Close'].pct_change().iloc[-lookback_days:]
        std_val = returns.std()
        volatility = float(std_val.item() if hasattr(std_val, 'item') else std_val) * 100
        
        # Calculer MACD et ADX si disponibles
        macd_signal = MarketRegimeDetector._calculate_macd_signal(data)
        adx_signal = MarketRegimeDetector._calculate_adx_signal(data)
        
        # Déterminer le régime
        regime = MarketRegimeDetector._classify_regime(
            current_price, sma_short_val, sma_long_val, slope_pct, volatility,
            macd_signal, adx_signal
        )
        
        # Calculer la confiance améliorée
        confidence = MarketRegimeDetector._calculate_confidence_enhanced(
            current_price, sma_short_val, sma_long_val, slope_pct,
            macd_signal, adx_signal
        )
        
        # Calculer la force de la tendance
        trend_strength = abs(slope_pct) / (volatility + 0.001) if volatility > 0 else 0
        
        return {
            'regime': regime,
            'confidence': confidence,
            'trend_strength': trend_strength,
            'slope': slope_pct,
            'volatility': volatility,
            'price': current_price,
            'sma_short': sma_short_val,
            'sma_long': sma_long_val,
            'macd_signal': macd_signal,
            'adx_signal': adx_signal,
            'details': f"Prix={current_price:.2f}, SMA{sma_short}={sma_short_val:.2f}, SMA{sma_long}={sma_long_val:.2f}, "
                      f"Pente={slope_pct:.2f}%, Vol={volatility:.2f}%, MACD={macd_signal:.2f}, ADX={adx_signal:.2f}"
        }
    
    @staticmethod
    def _get_adaptive_sma_periods(data, lookback=60):
        """
        Determine les periodes SMA optimales basees sur la volatilite
        
        Args:
            data: DataFrame avec donnees de prix
            lookback: Periode pour calculer la volatilite
        
        Returns:
            Tuple (sma_short, sma_long) adaptes
        """
        if len(data) < lookback:
            return (50, 200)
        
        # Calculer la volatilité annualisée
        returns = data['Close'].pct_change().iloc[-lookback:]
        volatility = returns.std() * np.sqrt(252) * 100  # Annualisée en %
        
        # Adapter les périodes SMA selon la volatilité
        if volatility > 40:  # Très volatile
            return (20, 50)   # SMA très court pour réagir vite
        elif volatility > 25:  # Volatile
            return (30, 100)  # SMA court
        elif volatility > 15:  # Modéré
            return (50, 150)  # SMA standard
        else:  # Faible volatilité
            return (50, 200)  # SMA long (défaut)
    
    @staticmethod
    def _calculate_macd_signal(data, fast=12, slow=26, signal=9):
        """
        Calcule le signal MACD (-1 a 1)
        
        Returns:
            Valeur entre -1 (bearish) et 1 (bullish)
        """
        if len(data) < slow + signal:
            return 0.0
        
        ema_fast = data['Close'].ewm(span=fast, adjust=False).mean()
        ema_slow = data['Close'].ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        # Normaliser le signal (-1 à 1)
        hist_val = float(histogram.iloc[-1])
        macd_range = float(histogram.abs().max()) if len(histogram) > 0 else 1.0
        
        if macd_range > 0:
            signal_val = np.clip(hist_val / macd_range, -1, 1)
        else:
            signal_val = 0.0
        
        return signal_val
    
    @staticmethod
    def _calculate_adx_signal(data, period=14):
        """
        Calcule le signal ADX (0 a 1) et direction (+DI/-DI)
        
        Returns:
            Valeur entre 0 (pas de tendance) et 1 (tendance forte)
        """
        if len(data) < period + 1:
            return 0.0
        
        # Calculer +DM et -DM
        high = data['High']
        low = data['Low']
        close = data['Close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        # Calculer TR (True Range)
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculer ATR, +DI, -DI
        atr = tr.rolling(window=period).mean()
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr.replace(0, np.nan))
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr.replace(0, np.nan))
        
        # Calculer DX et ADX
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)) * 100
        adx = dx.rolling(window=period).mean()
        
        # Normaliser ADX (0 à 1)
        adx_val = float(adx.iloc[-1]) if not pd.isna(adx.iloc[-1]) else 0.0
        signal_val = min(adx_val / 50.0, 1.0)  # ADX > 50 = tendance très forte
        
        return signal_val

    
    @staticmethod
    def _classify_regime(price, sma_short, sma_long, slope_pct, volatility, macd_signal=0, adx_signal=0):
        """Classifie le regime base sur les indicateurs avances"""
        
        # Convertir en floats pour éviter les Series ambiguës
        try:
            price = float(price)
            sma_short = float(sma_short)
            sma_long = float(sma_long)
            slope_pct = float(slope_pct)
            macd_signal = float(macd_signal)
            adx_signal = float(adx_signal)
        except (TypeError, ValueError):
            return 'UNKNOWN'
        
        # Vérifier si on a des valeurs valides
        if pd.isna(sma_short) or pd.isna(sma_long) or pd.isna(slope_pct):
            return 'UNKNOWN'
        
        # Pondération des signaux
        sma_bullish = price > sma_short and sma_short > sma_long
        sma_bearish = price < sma_short and sma_short < sma_long
        macd_bullish = macd_signal > 0.2
        macd_bearish = macd_signal < -0.2
        strong_trend = adx_signal > 0.5  # ADX > 25 (normalisé)
        
        # BULL: SMAs + MACD alignés, tendance forte
        if sma_bullish and slope_pct > 0.05:
            if macd_bullish and strong_trend:
                return 'BULL'
            elif macd_bullish or slope_pct > 0.1:
                return 'BULLISH'
        
        # BEAR: SMAs + MACD alignés, tendance forte
        if sma_bearish and slope_pct < -0.05:
            if macd_bearish and strong_trend:
                return 'BEAR'
            elif macd_bearish or slope_pct < -0.1:
                return 'BEARISH'
        
        # SIDEWAYS: Prix entre SMAs, faible pente, faible ADX
        if abs(slope_pct) < 0.1 and not strong_trend:
            if sma_long * 0.98 < price < sma_short * 1.02:
                return 'SIDEWAYS'
        
        # CONSOLIDATION: Transition ou faible momentum
        if abs(slope_pct) < 0.05 or abs(macd_signal) < 0.1:
            return 'CONSOLIDATION'
        
        # Par défaut selon prix vs SMA long
        if price > sma_long:
            return 'BULLISH'
        else:
            return 'BEARISH'

    
    @staticmethod
    def _calculate_confidence_enhanced(price, sma_short, sma_long, slope_pct, macd_signal=0, adx_signal=0):
        """Calcule le niveau de confiance ameliore du regime (0-1) avec MACD et ADX"""
        
        # Convertir en floats
        try:
            sma_short = float(sma_short)
            sma_long = float(sma_long)
            slope_pct = float(slope_pct)
            macd_signal = float(macd_signal)
            adx_signal = float(adx_signal)
        except (TypeError, ValueError):
            return 0.0
        
        if pd.isna(sma_short) or pd.isna(sma_long):
            return 0.0
        
        # Distance entre les SMAs (normalisée)
        sma_diff = abs(sma_short - sma_long)
        sma_confidence = min(sma_diff / sma_long if sma_long > 0 else 0, 0.25)  # Max 0.25
        
        # Pente (momentum)
        slope_confidence = min(abs(slope_pct) / 0.5, 0.30)  # Max 0.30 (pente 0.5% = max)
        
        # MACD alignment (signal cohérent)
        macd_alignment = abs(macd_signal)  # 0 à 1
        macd_confidence = macd_alignment * 0.25  # Max 0.25
        
        # ADX (force de tendance)
        adx_confidence = adx_signal * 0.20  # Max 0.20
        
        # Bonus si tous les signaux sont alignés
        alignment_bonus = 0.0
        if (slope_pct > 0 and macd_signal > 0) or (slope_pct < 0 and macd_signal < 0):
            alignment_bonus = 0.10  # +10% si MACD et pente alignés
        
        total_confidence = sma_confidence + slope_confidence + macd_confidence + adx_confidence + alignment_bonus
        return min(total_confidence, 1.0)
    
    @staticmethod
    def grid_search_thresholds(data, param_grid=None):
        """
        Grid search pour optimiser les thresholds de détection de régime
        
        Args:
            data: DataFrame avec données historiques
            param_grid: Dict avec les paramètres à tester
                        ex: {'slope_threshold': [0.05, 0.1, 0.15], 
                             'adx_threshold': [0.3, 0.5, 0.7]}
        
        Returns:
            Meilleurs paramètres et score
        """
        if param_grid is None:
            param_grid = {
                'slope_threshold': [0.03, 0.05, 0.08, 0.1, 0.15],
                'adx_threshold': [0.3, 0.4, 0.5, 0.6],
                'macd_threshold': [0.15, 0.2, 0.25, 0.3]
            }
        
        best_score = 0
        best_params = {}
        results = []
        
        # Générer toutes les combinaisons
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        
        for combination in product(*values):
            params = dict(zip(keys, combination))
            
            # Tester ces paramètres
            score = MarketRegimeDetector._evaluate_params(data, params)
            results.append({**params, 'score': score})
            
            if score > best_score:
                best_score = score
                best_params = params.copy()
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'all_results': pd.DataFrame(results)
        }
    
    @staticmethod
    def _evaluate_params(data, params):
        """
        Évalue la qualité des paramètres sur les données historiques
        
        Score basé sur:
        - Stabilité des régimes (moins de changements = mieux)
        - Confiance moyenne élevée
        - Distribution équilibrée des régimes
        """
        # Simuler la détection avec ces paramètres
        regimes = []
        confidences = []
        
        lookback = min(252, len(data))  # 1 an de données
        
        for i in range(lookback, len(data)):
            subset = data.iloc[:i+1]
            
            # Détecter avec paramètres personnalisés
            info = MarketRegimeDetector.detect_regime(subset)
            regimes.append(info['regime'])
            confidences.append(info['confidence'])
        
        # Calculer le score
        if len(regimes) < 10:
            return 0.0
        
        # 1. Stabilité (pénaliser les changements fréquents)
        regime_changes = sum(1 for i in range(1, len(regimes)) if regimes[i] != regimes[i-1])
        stability_score = 1.0 - (regime_changes / len(regimes))
        
        # 2. Confiance moyenne
        avg_confidence = np.mean(confidences)
        
        # 3. Distribution (pénaliser si un régime domine trop)
        regime_counts = pd.Series(regimes).value_counts()
        max_pct = regime_counts.max() / len(regimes)
        balance_score = 1.0 - abs(max_pct - 0.5)  # Idéal: 50% pour le plus grand
        
        # Score composite
        total_score = (stability_score * 0.3 + avg_confidence * 0.5 + balance_score * 0.2)
        
        return total_score

    
    @staticmethod
    def get_regime_history(data, periods=60, sma_short=50, sma_long=200, use_adaptive_sma=True):
        """Retourne l'historique des régimes pour chaque jour avec indicateurs avancés"""
        
        regimes = []
        lookback = min(periods, len(data))
        
        for i in range(len(data) - lookback, len(data)):
            subset = data.iloc[:i+1]
            regime_info = MarketRegimeDetector.detect_regime(
                subset, sma_short=sma_short, sma_long=sma_long, 
                use_adaptive_sma=use_adaptive_sma
            )
            regimes.append({
                'date': data.index[i],
                'regime': regime_info['regime'],
                'confidence': regime_info['confidence'],
                'trend_strength': regime_info['trend_strength'],
                'slope': regime_info['slope'],
                'volatility': regime_info['volatility'],
                'macd_signal': regime_info.get('macd_signal', 0),
                'adx_signal': regime_info.get('adx_signal', 0)
            })
        
        return pd.DataFrame(regimes)

    
    @staticmethod
    def get_regime_statistics(data, periods=252, use_adaptive_sma=True):
        """Retourne les statistiques des régimes sur la période avec métriques avancées"""
        
        history = MarketRegimeDetector.get_regime_history(data, periods=periods, use_adaptive_sma=use_adaptive_sma)
        
        if len(history) == 0:
            return {}
        
        regime_counts = history['regime'].value_counts()
        regime_pcts = (regime_counts / len(history) * 100).to_dict()
        
        # Calculer les transitions de régime
        regime_changes = sum(1 for i in range(1, len(history)) 
                           if history['regime'].iloc[i] != history['regime'].iloc[i-1])
        
        return {
            'total_days': len(history),
            'regime_distribution': regime_counts.to_dict(),
            'regime_percentages': regime_pcts,
            'most_common': history['regime'].mode()[0] if len(history) > 0 else 'UNKNOWN',
            'avg_confidence': history['confidence'].mean(),
            'avg_trend_strength': history['trend_strength'].mean(),
            'avg_volatility': history['volatility'].mean(),
            'regime_changes': regime_changes,
            'stability_score': 1.0 - (regime_changes / len(history)),
            'avg_macd_signal': history['macd_signal'].mean(),
            'avg_adx_signal': history['adx_signal'].mean()
        }
