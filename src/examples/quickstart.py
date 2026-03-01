"""
Script de démarrage rapide - Premier lancement
"""
import os
import subprocess
import sys


def install_dependencies():
    """Installe les dépendances"""
    print("📦 Installation des dépendances...")
    print("-" * 50)
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("\n✅ Dépendances installées!")
        return True
    except Exception as e:
        print(f"\n❌ Erreur lors de l'installation: {e}")
        return False


def create_directories():
    """Crée les dossiers nécessaires"""
    print("\n📁 Création des dossiers...")
    
    dirs = ['data', 'models', 'reports', 'reports/plots']
    for directory in dirs:
        os.makedirs(directory, exist_ok=True)
        print(f"   ✓ {directory}/")
    
    print("✅ Dossiers créés!")


def main():
    """Lance le setup et le trading pipeline"""
    
    print("\n" + "="*70)
    print("🤖 TRADING ALGORITHMIQUE - PREMIER DÉMARRAGE")
    print("="*70)
    
    # 1. Installer les dépendances
    if not install_dependencies():
        sys.exit(1)
    
    # 2. Créer les dossiers
    create_directories()
    
    # 3. Lancer le pipeline
    print("\n" + "="*70)
    print("🚀 Lancement du pipeline de trading...")
    print("="*70)
    
    try:
        from main import TradingPipeline
        
        pipeline = TradingPipeline(ticker='AAPL', model_type='gradient_boosting')
        report = pipeline.run(start_date='2022-01-01')
        
        print("\n" + "="*70)
        print("✅ SUCCÈS! Pipeline complété!")
        print("="*70)
        print("\n📊 Résultats:")
        print(f"   - Rapport: reports/backtest_report_*.txt")
        print(f"   - Graphiques: reports/plots/")
        print(f"   - Modèle: models/")
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
