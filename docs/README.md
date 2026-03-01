# 🤖 Trading Algorithme Automatique

Un système complet d'entraînement et backtesting d'un algorithme de trading utilisant le machine learning sur des données réelles.

## 📋 Vue d'ensemble

Ce projet implémente un pipeline complet pour :
1. **Télécharger** des données réelles du marché financier
2. **Créer** des indicateurs techniques (SMA, RSI, MACD, Bollinger Bands, etc.)
3. **Entraîner** un modèle ML pour prédire les mouvements de prix
4. **Backtester** la stratégie sur des données historiques
5. **Analyser** les performances et le taux d'erreur

## 🚀 Installation

```bash
# Installer les dépendances
pip install -r requirements.txt
```

## 📁 Structure du projet

```
├── main.py                      # Script principal - Orchestration
├── data_fetcher.py             # Téléchargement des données réelles
├── feature_engineering.py      # Création des indicateurs techniques
├── trading_model.py            # Modèle ML de prédiction
├── backtest_engine.py          # Simulation des trades
├── requirements.txt            # Dépendances Python
├── data/                       # Données téléchargées
├── models/                     # Modèles sauvegardés
└── reports/                    # Rapports et graphiques
```

## 💻 Utilisation rapide

```python
from main import TradingPipeline

# Créer et lancer le pipeline
pipeline = TradingPipeline(ticker='AAPL', model_type='gradient_boosting')
report = pipeline.run(start_date='2022-01-01')
```

Ou directement via terminal:
```bash
python main.py
```

## 🎯 Fonctionnalités principales

### 1. Data Fetcher (`data_fetcher.py`)
- Télécharge les données réelles via Yahoo Finance
- Support de multiples tickers
- Nettoyage automatique des données
- Cache local des données

**Exemple:**
```python
from data_fetcher import DataFetcher

fetcher = DataFetcher()
data = fetcher.fetch_stock_data('AAPL', start_date='2022-01-01')
```

### 2. Feature Engineering (`feature_engineering.py`)
Crée **15+** indicateurs techniques:
- **Moyennes mobiles:** SMA, EMA
- **Momentum:** MACD, RSI, ROC
- **Volatilité:** Bollinger Bands, ATR
- **Volume:** Volume ratio
- **Target variable:** Prédiction 5 jours en avant

**Exemple:**
```python
from feature_engineering import FeatureEngineering

fe = FeatureEngineering()
data = fe.add_technical_indicators(data)
data['Target'] = fe.create_target_variable(data, prediction_window=5)
```

### 3. Trading Model (`trading_model.py`)
Trois modèles disponibles:
- **Gradient Boosting** (recommandé - meilleur équilibre)
- **Random Forest** (robuste, élevé overfitting)
- **Neural Network** (flexible mais plus lent)

**Exemple:**
```python
from trading_model import TradingModel

model = TradingModel(model_type='gradient_boosting')
model.train(X_train, y_train)
metrics = model.evaluate(X_test, y_test)
```

**Résultats du modèle:**
- Accuracy: ~60-65%
- Precision: ~55-60%
- Recall: ~50-55%
- ROC-AUC: ~0.60-0.65

### 4. Backtest Engine (`backtest_engine.py`)
Simule l'exécution des trades:
- Gère le portefeuille (cash, positions)
- Calcule les profits/pertes
- Track win rate et drawdown
- Génère rapports détaillés

**Métriques calculées:**
- Rendement total
- Taux de réussite des trades
- Profit/Perte moyen
- Maximum Drawdown
- Historique complet des transactions

## 📊 Sorties

Après l'exécution, vous recevrez:

### 1. Rapport texte (reports/backtest_report_*.txt)
```
RAPPORT DE TRADING AUTOMATIQUE
==============================
Période: 2022-01-01 -> 2024-02-22
Capital initial: $10,000.00
Valeur finale: $12,450.75
Rendement: 24.51%

Nombre de trades: 45
Taux de réussite: 62.22%
Profit moyen: $85.50
Perte moyenne: -$120.30
Max Drawdown: -18.5%
```

### 2. Graphiques
- `price_indicators_*.png`: Prix + SMA + RSI
- `portfolio_performance_*.png`: Évolution du portefeuille

### 3. Modèles
- `models/*.pkl`: Modèle entraîné sauvegardé

## 🔧 Configuration personnalisée

Éditez le fichier `main.py`:

```python
# Configuration
TICKERS = ['AAPL', 'MSFT', 'GOOGL']  # Plusieurs actions
MODEL_TYPE = 'gradient_boosting'   # Type de modèle
START_DATE = '2022-01-01'          # Période d'entraînement
```

## 📈 Interprétation des résultats

### Taux d'erreur du modèle
- **Accuracy 60%**: Le modèle prédit correctement la direction 60% des fois
- **Precision 55%**: Quand il dit "acheter", c'est correct 55% des fois
- **Recall 50%**: Il détecte 50% des vrais signaux d'achat

### Performance du backtest
- **Rendement positif**: La stratégie est rentable
- **Win rate > 50%**: Plus de trades gagnants que perdants
- **Max Drawdown < 20%**: Risques acceptables

## ⚠️ Limitations et disclaimers

1. **Backtesting n'est pas garanti**: Les performances passées ne garantissent pas les résultats futurs
2. **Slippage et commissions**: Non inclus dans le backtest
3. **Conditions de marché changent**: Le modèle peut nécessiter ré-entraînement régulier
4. **Risque réel**: Ne pas utiliser en trading réel sans validation supplémentaire

## 🎓 Améliorations possibles

- [ ] Ajouter des frais de transaction et slippage
- [ ] Implémentation d'un risk management (stop loss)
- [ ] Ensemble de modèles (ensemble learning)
- [ ] Walktesting (validation forward)
- [ ] Optimisation des paramètres (hyperparameter tuning)
- [ ] Données crypto et forex
- [ ] Exécution réelle avec APIs (Interactive Brokers, etc.)

## 📚 Ressources

- [Yahoo Finance API](https://finance.yahoo.com/)
- [Indicateurs techniques](https://school.stockcharts.com/)
- [Scikit-Learn ML](https://scikit-learn.org/)
- [Pandas Documentation](https://pandas.pydata.org/)

## 📧 Support

Pour questions ou améliorations, consultez le code source ou la documentation.

---

**⚠️ Disclaimer légal:** Ce projet est à des fins éducatives uniquement. Consultez un conseiller financier avant de trader réellement.
