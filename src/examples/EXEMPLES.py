"""
EXEMPLES D'UTILISATION
======================

Voici différentes façons d'utiliser le système de trading automatique.
"""

# ============================================================================
# EXEMPLE 1: Utilisation basique (recommandée pour débuter)
# ============================================================================
from main import TradingPipeline

# Lancer le pipeline complet
pipeline = TradingPipeline(ticker='AAPL', model_type='gradient_boosting')
report = pipeline.run(start_date='2022-01-01')


# ============================================================================
# EXEMPLE 2: Télécharger des données réelles
# ============================================================================
from data_fetcher import DataFetcher

fetcher = DataFetcher()

# Une seule action
data_aapl = fetcher.fetch_stock_data('AAPL', start_date='2022-01-01')
print(data_aapl.head())

# Multiples actions
tickers = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']
data = fetcher.fetch_multiple(tickers, start_date='2022-01-01')


# ============================================================================
# EXEMPLE 3: Créer les indicateurs techniques
# ============================================================================
from feature_engineering import FeatureEngineering

fe = FeatureEngineering()

# Ajouter tous les indicateurs
data_with_indicators = fe.add_technical_indicators(data_aapl)

# Créer la variable cible
data_with_indicators['Target'] = fe.create_target_variable(
    data_with_indicators, 
    prediction_window=5,  # Prédire 5 jours en avant
    threshold=0.01  # 1% de variation minimum
)

print("Indicateurs disponibles:", data_with_indicators.columns.tolist())


# ============================================================================
# EXEMPLE 4: Entraîner un modèle
# ============================================================================
from trading_model import TradingModel

# Préparer les données
X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(data_with_indicators)

# Essayer différents modèles
models = {
    'gradient_boosting': 'Meilleur équilibre',
    'random_forest': 'Robuste mais lent',
    'neural_network': 'Flexible mais complexe'
}

for model_name, description in models.items():
    print(f"\n🤖 Entraînement {model_name} ({description})...")
    
    model = TradingModel(model_type=model_name)
    model.train(X_train, y_train)
    
    # Évaluer
    metrics = model.evaluate(X_test, y_test)
    print(f"   F1-Score: {metrics['f1']:.4f}")
    print(f"   Accuracy: {metrics['accuracy']:.4f}")
    
    # Sauvegarder le meilleur modèle
    # model.save(f'models/{model_name}.pkl')


# ============================================================================
# EXEMPLE 5: Backtester une stratégie
# ============================================================================
from backtest_engine import BacktestEngine

# Prédictions
predictions = model.predict(X_test)

# Lancer le backtest
engine = BacktestEngine(
    initial_capital=10000,
    position_size_pct=0.95,  # Utiliser 95% du capital par trade
    stop_loss_pct=-2.0,      # Stop Loss à -2%
    take_profit_pct=5.0,     # Take Profit à +5%
    use_trend_filter=True    # Filtrer avec SMA 200
)

report = engine.run_backtest(
    data_with_indicators,
    model,
    X_test,
    X_test.index,
    predictions
)

# Afficher le rapport
engine.print_report(report)


# ============================================================================
# EXEMPLE 6: Analyse avancée
# ============================================================================
from advanced_analysis import AdvancedAnalysis

analysis = AdvancedAnalysis(report)
analysis.generate_summary()
analysis.plot_trade_analysis()


# ============================================================================
# EXEMPLE 7: Prédictions sur de nouvelles données
# ============================================================================
# Récupérer les données de cette semaine
from datetime import datetime, timedelta

end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

new_data = fetcher.fetch_stock_data('AAPL', start_date=start_date, end_date=end_date)

# Ajouter les indicateurs
new_data = fe.add_technical_indicators(new_data)
new_data_clean = new_data.dropna()

# Prédire sur les nouvelles données
X_new, _, _, _, _ = fe.prepare_training_data(new_data)
# Note: utiliser le même scaler que l'entraînement

predictions = model.predict(X_new)
probabilities = model.predict_proba(X_new)

# Afficher les prédictions récentes
print("\n📊 Prédictions récentes:")
for date, pred, proba in zip(X_new.index[-5:], predictions[-5:], probabilities[-5:]):
    signal = "🟢 ACHAT" if pred == 1 else "🔴 VENTE"
    confidence = proba[pred] * 100
    print(f"{date.date()}: {signal} (confiance: {confidence:.1f}%)")


# ============================================================================
# EXEMPLE 8: Optimisation des hyperparamètres (avancé)
# ============================================================================
from sklearn.model_selection import GridSearchCV
from sklearn.ensemble import GradientBoostingClassifier

# Définir la grille
param_grid = {
    'n_estimators': [100, 200, 300],
    'learning_rate': [0.01, 0.05, 0.1],
    'max_depth': [3, 5, 7],
    'min_samples_split': [5, 10, 15]
}

# Grid search
gb = GradientBoostingClassifier(random_state=42)
grid_search = GridSearchCV(gb, param_grid, cv=5, scoring='f1', n_jobs=-1)
grid_search.fit(X_train, y_train)

print(f"\n🎯 Meilleurs paramètres: {grid_search.best_params_}")
print(f"📊 Meilleur F1-Score: {grid_search.best_score_:.4f}")

# Utiliser le meilleur modèle
best_model = grid_search.best_estimator_


# ============================================================================
# EXEMPLE 9: Comparaison de plusieurs actions
# ============================================================================
results = {}

for ticker in ['AAPL', 'MSFT', 'GOOGL']:
    pipeline = TradingPipeline(ticker=ticker)
    report = pipeline.run(start_date='2022-01-01')
    
    results[ticker] = {
        'return': report['total_return_pct'],
        'win_rate': report['win_rate'],
        'max_dd': report['max_drawdown']
    }

# Afficher les résultats
import pandas as pd
df_results = pd.DataFrame(results).T
print("\n📊 Résultats par action:")
print(df_results)


# ============================================================================
# EXEMPLE 10: Charger un modèle sauvegardé
# ============================================================================
# Charger un modèle précédent
model = TradingModel()
model.load('models/AAPL_gradient_boosting.pkl')

# Utiliser pour prédictions
predictions = model.predict(X_new)


# ============================================================================
# EXEMPLE 11: Analyse de sensibilité
# ============================================================================
# Tester différents periods pour les indicateurs techniques

for period in [10, 20, 30]:
    print(f"\n📊 Test avec période {period}...")
    
    # Créer les features avec different period
    data_test = data_aapl.copy()
    data_test['SMA'] = data_test['Close'].rolling(window=period).mean()
    data_test['RSI'] = fe._calculate_rsi(data_test['Close'], period=period)
    
    # Entraîner et tester
    # ... continuer avec le pipeline


print("\n✅ Exemples complétés!")
