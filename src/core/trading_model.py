"""
Module pour le modèle de trading
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.utils.class_weight import compute_sample_weight
import joblib
import os


class TradingModel:
    """Modèle ML pour prédire les mouvements de prix"""
    
    def __init__(self, model_type='gradient_boosting'):
        """
        Initialise le modèle
        
        Args:
            model_type: 'random_forest', 'gradient_boosting', 'neural_network'
        """
        self.model_type = model_type
        self.model = None
        self.is_trained = False
        
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=15,
                min_samples_split=5,
                min_samples_leaf=2,
                class_weight='balanced',
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(
                n_estimators=100,       # réduit pour éviter l'overfitting
                learning_rate=0.05,
                max_depth=3,            # 5→3 : modèle moins profond = moins de mémorisation
                min_samples_split=20,   # 10→20 : nécessite plus de données pour splitter
                min_samples_leaf=15,    # 5→15 : feuilles plus larges = plus de régularisation
                subsample=0.7,          # 0.8→0.7 : stochastique plus agressif
                random_state=42
            )
        elif model_type == 'neural_network':
            self.model = MLPClassifier(
                hidden_layer_sizes=(128, 64, 32),
                learning_rate_init=0.001,
                max_iter=500,
                batch_size=32,
                random_state=42,
                early_stopping=True
            )
        else:
            raise ValueError(f"Model type {model_type} not supported")
        self.sample_weight = None
    
    def train(self, X_train, y_train, X_val=None, y_val=None):
        """
        Entraine le modele
        
        Args:
            X_train: Features d'entrainement
            y_train: Target d'entrainement
            X_val: Features de validation (optionnel)
            y_val: Target de validation (optionnel)
        
        Returns:
            Scores de validation croisee
        """
        print(f"\n[ROBOT] Entrainement du modele ({self.model_type})...")
        print(f"   Donnees: {len(X_train)} echantillons, {X_train.shape[1]} features")

        # Calculer sample weights (sur l'ensemble du train pour le fit final)
        sample_weight = compute_sample_weight('balanced', y_train)

        # Entraîner le modèle sur l'ensemble du jeu train
        if self.model_type == 'gradient_boosting':
            self.model.fit(X_train, y_train, sample_weight=sample_weight)
        else:
            self.model.fit(X_train, y_train)
        self.is_trained = True

        # ----------------------------------------------------------------
        # Walk-forward CV avec sample_weight correctement recalculé par fold
        # ----------------------------------------------------------------
        # Problème de cross_val_score(fit_params={'sample_weight': w}):
        # sklearn passe le MÊME vecteur w (taille n) à chaque fold dont le train
        # a une taille différente → IndexError ou poids incorrects.
        # Solution: boucle manuelle — sw recalculé sur le fold_train exact.
        from sklearn.base import clone as _clone
        from sklearn.metrics import f1_score as _f1

        tscv = TimeSeriesSplit(n_splits=5)
        cv_f1_scores = []
        for fold_tr_idx, fold_val_idx in tscv.split(X_train):
            X_f_tr = X_train.iloc[fold_tr_idx]
            X_f_val = X_train.iloc[fold_val_idx]
            y_f_tr = y_train.iloc[fold_tr_idx]
            y_f_val = y_train.iloc[fold_val_idx]

            fold_model = _clone(self.model)
            sw_fold = compute_sample_weight('balanced', y_f_tr)
            try:
                fold_model.fit(X_f_tr, y_f_tr, sample_weight=sw_fold)
            except TypeError:
                fold_model.fit(X_f_tr, y_f_tr)

            y_pred_fold = fold_model.predict(X_f_val)
            cv_f1_scores.append(_f1(y_f_val, y_pred_fold, zero_division=0))

        cv_scores = np.array(cv_f1_scores)
        print(f"   Cross-validation F1 (TimeSeriesSplit, sw/fold): "
              f"{cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

        # Accuracy d'entraînement
        train_score = self.model.score(X_train, y_train)
        print(f"   Training Accuracy: {train_score:.4f}")

        return cv_scores
    
    def predict(self, X):
        """Effectue une prédiction"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")
        
        return self.model.predict(X)
    
    def predict_proba(self, X):
        """Retourne les probabilités de prédiction"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")
        
        return self.model.predict_proba(X)
    
    def evaluate(self, X_test, y_test):
        """
        Évalue le modèle sur les données de test
        
        Returns:
            Dictionnaire avec métriques
        """
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, roc_auc_score
        
        y_pred = self.predict(X_test)
        y_proba = self.predict_proba(X_test)[:, 1]
        
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_proba),
            'confusion_matrix': confusion_matrix(y_test, y_pred)
        }
        
        return metrics
    
    def evaluate_financial(
        self,
        X_test,
        y_test,
        close_prices: 'pd.Series',
        prediction_window: int = 5,
        threshold: float = 0.5,
        commission_pct: float = 0.1,
        slippage_pct: float = 0.05,
    ) -> dict:
        """
        Évalue le modèle avec des métriques financières (Sharpe, profit factor, expectancy).

        Contrairement à evaluate() (F1, AUC), cette méthode calcule ce qui compte
        réellement en trading: la profitabilité nette des signaux générés.

        Args:
            X_test           : Features de test (DataFrame avec index datetime)
            y_test           : Labels réels (non utilisés pour le sizing — juste pour comparaison)
            close_prices     : Série Close originale (même index que X_test)
            prediction_window: Fenêtre forward en jours
            threshold        : Seuil de probabilité pour déclencher BUY
            commission_pct   : Commission aller+retour totale en %
            slippage_pct     : Slippage aller+retour total en %

        Returns:
            Dict avec: sharpe, profit_factor, expectancy, win_rate, n_trades, ...
        """
        try:
            from ml_optimizer import compute_financial_metrics, _compute_forward_returns
        except ImportError:
            from .ml_optimizer import compute_financial_metrics, _compute_forward_returns

        probas = self.predict_proba(X_test)[:, 1]
        predictions = (probas >= threshold).astype(int)

        # Retours forward pour les dates de test
        fwd_returns = _compute_forward_returns(close_prices, X_test.index, prediction_window)

        # Filtrer les NaN (fin de série)
        valid = ~np.isnan(fwd_returns)
        if valid.sum() < 2:
            return {}

        return compute_financial_metrics(
            predictions[valid], fwd_returns[valid], commission_pct, slippage_pct
        )

    def get_feature_importance(self, X_columns):
        """Retourne l'importance de chaque feature"""
        if not hasattr(self.model, 'feature_importances_'):
            return None
        
        importances = self.model.feature_importances_
        df_importance = pd.DataFrame({
            'feature': X_columns,
            'importance': importances
        }).sort_values('importance', ascending=False)
        
        return df_importance
    
    def save(self, filepath):
        """Sauvegarde le modele"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self.model, filepath)
        print(f"[CHECK] Modele sauvegarde: {filepath}")
    
    def load(self, filepath):
        """Charge le modele"""
        self.model = joblib.load(filepath)
        self.is_trained = True
        print(f"[CHECK] Modele charge: {filepath}")


if __name__ == "__main__":
    # Test
    from feature_engineering import FeatureEngineering
    from data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    data = fetcher.fetch_stock_data('AAPL', start_date='2023-01-01')
    
    fe = FeatureEngineering()
    data = fe.add_technical_indicators(data)
    data['Target'] = fe.create_target_variable(data)
    
    X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(data)
    
    model = TradingModel(model_type='gradient_boosting')
    model.train(X_train, y_train)
    
    metrics = model.evaluate(X_test, y_test)
    print("\n[CHART] Resultats de test:")
    for key, value in metrics.items():
        if key != 'confusion_matrix':
            print(f"   {key}: {value:.4f}")
