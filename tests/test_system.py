"""
Script de test - Vérifie que tout fonctionne avant le vrai pipeline
"""
import sys
import os


def test_imports():
    """Teste que toutes les imports fonctionnent"""
    print("\n" + "="*70)
    print("🔧 TEST 1: Imports Python")
    print("="*70)
    
    try:
        print("  Vérification des imports...")
        import pandas as pd
        print("  ✓ pandas")
        import numpy as np
        print("  ✓ numpy")
        from sklearn.ensemble import GradientBoostingClassifier
        print("  ✓ scikit-learn")
        import yfinance as yf
        print("  ✓ yfinance")
        import matplotlib.pyplot as plt
        print("  ✓ matplotlib")
        
        print("\n✅ TOUS LES IMPORTS RÉUSSIS!")
        return True
    except ImportError as e:
        print(f"\n❌ ERREUR D'IMPORT: {e}")
        print("\nSolution: pip install -r requirements.txt")
        return False


def test_data_fetcher():
    """Teste le téléchargement de données"""
    print("\n" + "="*70)
    print("🔧 TEST 2: Téléchargement de Données")
    print("="*70)
    
    try:
        from data_fetcher import DataFetcher
        
        print("  Téléchargement de 3 mois de données AAPL...")
        fetcher = DataFetcher()
        data = fetcher.fetch_stock_data('AAPL', start_date='2024-01-01', end_date='2024-04-01')
        
        print(f"  ✓ Récupéré {len(data)} jours de données")
        print(f"  ✓ Colonnes: {', '.join(data.columns.tolist())}")
        print(f"  ✓ Prix: ${data['Close'].iloc[0]:.2f} -> ${data['Close'].iloc[-1]:.2f}")
        
        print("\n✅ TÉLÉCHARGEMENT RÉUSSI!")
        return data
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        return None


def test_features(data):
    """Teste la création de features"""
    print("\n" + "="*70)
    print("🔧 TEST 3: Création des Indicateurs Techniques")
    print("="*70)
    
    try:
        from feature_engineering import FeatureEngineering
        
        print("  Création des indicateurs...")
        fe = FeatureEngineering()
        data_features = fe.add_technical_indicators(data)
        
        print(f"  ✓ Ajouté {len(data_features.columns) - len(data.columns)} colonnes")
        print(f"  ✓ Nombre total de features: {len(data_features.columns)}")
        
        # Test target
        data_features['Target'] = fe.create_target_variable(data_features)
        targets = data_features['Target'].value_counts()
        print(f"  ✓ Variable cible créée:")
        print(f"    - Signaux d'achat (1): {targets[1] if 1 in targets.index else 0}")
        print(f"    - Signaux de vente (0): {targets[0] if 0 in targets.index else 0}")
        
        print("\n✅ FEATURES CRÉÉES!")
        return data_features
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_model(data_features):
    """Teste l'entraînement du modèle"""
    print("\n" + "="*70)
    print("🔧 TEST 4: Entraînement du Modèle ML")
    print("="*70)
    
    try:
        from feature_engineering import FeatureEngineering
        from trading_model import TradingModel
        
        print("  Préparation des données...")
        fe = FeatureEngineering()
        X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(data_features)
        
        print(f"  ✓ Données d'entraînement: {len(X_train)} échantillons, {X_train.shape[1]} features")
        print(f"  ✓ Données de test: {len(X_test)} échantillons")
        
        print("\n  Entraînement du modèle (Gradient Boosting)...")
        model = TradingModel(model_type='gradient_boosting')
        model.train(X_train, y_train)
        
        print("\n  Évaluation du modèle...")
        metrics = model.evaluate(X_test, y_test)
        
        print(f"  ✓ Accuracy: {metrics['accuracy']:.4f}")
        print(f"  ✓ Precision: {metrics['precision']:.4f}")
        print(f"  ✓ Recall: {metrics['recall']:.4f}")
        print(f"  ✓ F1-Score: {metrics['f1']:.4f}")
        print(f"  ✓ ROC-AUC: {metrics['roc_auc']:.4f}")
        
        print("\n✅ MODÈLE ENTRAÎNÉ!")
        return model, X_test, y_test
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


def test_backtest(data, model, X_test, y_test):
    """Teste le backtesting"""
    print("\n" + "="*70)
    print("🔧 TEST 5: Backtesting")
    print("="*70)
    
    try:
        from backtest_engine import BacktestEngine
        
        print("  Génération des prédictions...")
        predictions = model.predict(X_test)
        
        print("  Lancement du backtest...")
        engine = BacktestEngine(initial_capital=10000, position_size_pct=0.95,
                               stop_loss_pct=-2.0, take_profit_pct=5.0, use_trend_filter=True)
        report = engine.run_backtest(data, model, X_test, X_test.index, predictions)
        
        print(f"\n  ✓ Rendement final: {report['total_return_pct']:.2f}%")
        print(f"  ✓ Nombre de trades: {report['total_trades']}")
        print(f"  ✓ Taux de réussite: {report['win_rate']:.2f}%")
        print(f"  ✓ Max Drawdown: {report['max_drawdown']:.2f}%")
        
        print("\n✅ BACKTEST COMPLÉTÉ!")
        return report
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Lance tous les tests"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "🧪 TEST DU SYSTÈME DE TRADING" + " "*24 + "║")
    print("╚" + "="*68 + "╝")
    
    # Test 1: Imports
    if not test_imports():
        print("\n❌ Les imports ont échoué. Impossible de continuer.")
        return False
    
    # Test 2: Data Fetcher
    data = test_data_fetcher()
    if data is None:
        print("\n⚠️  Could not fetch data. Check internet connection.")
        return False
    
    # Test 3: Features
    data_features = test_features(data)
    if data_features is None:
        print("\n❌ Feature engineering failed.")
        return False
    
    # Test 4: Model
    model, X_test, y_test = test_model(data_features)
    if model is None:
        print("\n❌ Model training failed.")
        return False
    
    # Test 5: Backtest
    report = test_backtest(data_features, model, X_test, y_test)
    if report is None:
        print("\n❌ Backtesting failed.")
        return False
    
    # Summary
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    print("✅ TOUS LES TESTS RÉUSSIS!")
    print("\n✨ Le système est prêt à l'emploi!")
    print("\n🚀 Prochaines étapes:")
    print("   1. python main.py  (pour lancer le pipeline complet)")
    print("   2. Consulter reports/  (pour les résultats)")
    print("   3. Lire README.md  (pour la documentation)")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
