"""
Script principal - Lance le pipeline complet de trading
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Ajouter les chemins des modules
project_root = os.path.abspath(os.path.dirname(__file__))
while os.path.basename(project_root) != 'algo trading' and project_root != os.path.dirname(project_root):
    project_root = os.path.dirname(project_root)

sys.path.insert(0, os.path.join(project_root, 'src', 'core'))
sys.path.insert(0, os.path.join(project_root, 'src', 'analysis'))
sys.path.insert(0, os.path.join(project_root, 'src', 'strategies'))

from data_fetcher import DataFetcher
from feature_engineering import FeatureEngineering
from trading_model import TradingModel
from backtest_engine import BacktestEngine


class TradingPipeline:
    """Pipeline complet: donnees -> features -> model -> backtest"""
    
    def __init__(self, ticker='AAPL', model_type='gradient_boosting'):
        self.ticker = ticker
        self.model_type = model_type
        self.data = None
        self.model = None
        self.backtest_report = None
    
    def run(self, start_date='2022-01-01'):
        """Lance le pipeline complet"""
        print("\n" + "="*70)
        print(f"[ROCKET] PIPELINE DE TRADING AUTOMATIQUE - {self.ticker}")
        print("="*70)
        
        # 1. Telecharger les donnees
        print("\n[1/5] Telechargement des donnees reelles...")
        self.data = self._fetch_data(start_date)
        
        # 2. Creer les features
        print("\n[2/5] Creation des indicateurs techniques...")
        self.data = self._create_features()
        
        # 3. Entrainer le modele
        print("\n[3/5] Entrainement du modele ML...")
        self.model = self._train_model()
        
        # 4. Backtester
        print("\n[4/5] Backtesting de la strategie...")
        self.backtest_report = self._run_backtest()
        
        # 5. Generer les rapports
        print("\n[5/5] Generation des rapports...")
        self._generate_reports()
        
        print("\n[CHECK] Pipeline complete!")
        return self.backtest_report
    
    def _fetch_data(self, start_date):
        """Telecharge les donnees"""
        fetcher = DataFetcher()
        data = fetcher.fetch_stock_data(self.ticker, start_date=start_date)
        return data
    
    def _create_features(self):
        """Cree les features/indicateurs"""
        fe = FeatureEngineering()
        data = fe.add_technical_indicators(self.data)
        data['Target'] = fe.create_target_variable(data, prediction_window=5)
        return data
    
    def _train_model(self):
        """Entraine le modele"""
        fe = FeatureEngineering()
        X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(self.data)
        
        # Creer et entrainer le modele
        model = TradingModel(model_type=self.model_type)
        model.train(X_train, y_train)
        
        # Evaluer
        metrics = model.evaluate(X_test, y_test)
        
        print(f"\n[CHART] Resultats de validation:")
        print(f"   Accuracy: {metrics['accuracy']:.4f}")
        print(f"   Precision: {metrics['precision']:.4f}")
        print(f"   Recall: {metrics['recall']:.4f}")
        print(f"   F1-Score: {metrics['f1']:.4f}")
        print(f"   ROC-AUC: {metrics['roc_auc']:.4f}")
        print(f"\n   Confusion Matrix:")
        print(f"   {metrics['confusion_matrix']}")
        
        # Feature importance
        importance = model.get_feature_importance(X_train.columns)
        if importance is not None:
            print(f"\n   Top 10 features:")
            print(importance.head(10).to_string())
        
        # Sauvegarder le modele
        model.save(f'models/{self.ticker}_{self.model_type}.pkl')
        
        # Garder les infos pour le backtest
        self.X_train = X_train
        self.X_test = X_test
        self.y_test = y_test
        self.scaler = scaler
        
        return model
    
    def _run_backtest(self):
        """Lance le backtest"""
        # Predictions sur les donnees de test
        predictions = self.model.predict(self.X_test)
        test_dates = self.X_test.index
        
        # Backtest
        engine = BacktestEngine(initial_capital=10000, position_size_pct=0.95, 
                               stop_loss_pct=-2.0, take_profit_pct=5.0, use_trend_filter=True)
        report = engine.run_backtest(self.data, self.model, self.X_test, test_dates, predictions)
        
        # Afficher le rapport
        engine.print_report(report)
        
        return report
    
    def _generate_reports(self):
        """Genere les rapports et visualisations"""
        os.makedirs('reports', exist_ok=True)
        
        # 1. Rapport texte
        self._save_text_report()
        
        # 2. Graphiques
        self._save_plots()
    
    def _save_text_report(self):
        """Sauvegarde un rapport texte"""
        report = self.backtest_report
        
        filename = f'reports/backtest_report_{self.ticker}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write(f"RAPPORT DE TRADING AUTOMATIQUE - {self.ticker}\n")
            f.write("="*70 + "\n\n")
            
            f.write(f"Date rapport: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Periode: {report['start_date']} -> {report['end_date']}\n\n")
            
            f.write("-"*70 + "\n")
            f.write("PERFORMANCE\n")
            f.write("-"*70 + "\n")
            f.write(f"Capital initial: ${report['initial_capital']:.2f}\n")
            f.write(f"Valeur finale: ${report['final_value']:.2f}\n")
            f.write(f"Rendement: {report['total_return_pct']:.2f}%\n")
            f.write(f"Profit/Perte: ${report['final_value'] - report['initial_capital']:.2f}\n\n")
            
            f.write("-"*70 + "\n")
            f.write("TRADES\n")
            f.write("-"*70 + "\n")
            f.write(f"Nombre total de trades: {report['total_trades']}\n")
            f.write(f"Achats: {report['buy_trades']}\n")
            f.write(f"Ventes: {report['sell_trades']}\n")
            f.write(f"Taux de reussite: {report['win_rate']:.2f}%\n")
            f.write(f"Profit moyen: ${report['avg_profit']:.2f}\n")
            f.write(f"Perte moyenne: ${report['avg_loss']:.2f}\n")
            f.write(f"Drawdown max: {report['max_drawdown']:.2f}%\n\n")
            
            f.write("-"*70 + "\n")
            f.write("MODELE\n")
            f.write("-"*70 + "\n")
            f.write(f"Type: {self.model_type}\n")
            f.write(f"Accuracy: {self.backtest_report.get('model_accuracy', 'N/A')}\n\n")
            
            if len(report['trades_df']) > 0:
                f.write("-"*70 + "\n")
                f.write("HISTORIQUE DES TRADES\n")
                f.write("-"*70 + "\n")
                f.write(report['trades_df'].to_string() + "\n")
        
        print(f"[CHECK] Rapport sauvegarde: {filename}")
    
    def _save_plots(self):
        """Sauvegarde les graphiques"""
        os.makedirs('reports/plots', exist_ok=True)
        
        # 1. Prix et signaux
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Graphique du prix
        ax1.plot(self.data.index, self.data['Close'], label='Prix', linewidth=2)
        ax1.plot(self.data.index, self.data['SMA_20'], label='SMA 20', alpha=0.7)
        ax1.plot(self.data.index, self.data['SMA_50'], label='SMA 50', alpha=0.7)
        ax1.set_title(f'Prix de {self.ticker} et Moyennes Mobiles', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Prix ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Graphique RSI
        ax2.plot(self.data.index, self.data['RSI'], label='RSI', linewidth=2)
        ax2.axhline(y=70, color='r', linestyle='--', alpha=0.5, label='Overbought')
        ax2.axhline(y=30, color='g', linestyle='--', alpha=0.5, label='Oversold')
        ax2.set_title('RSI (Relative Strength Index)', fontsize=14, fontweight='bold')
        ax2.set_ylabel('RSI')
        ax2.set_ylim([0, 100])
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_file = f'reports/plots/price_indicators_{self.ticker}.png'
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"[CHECK] Graphique sauvegarde: {plot_file}")
        plt.close()
        
        # 2. Performance du backtest
        report = self.backtest_report
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Valeur du portefeuille
        portfolio_values = report.get('portfolio_values', [report['initial_capital']])
        ax.plot(range(len(portfolio_values)), portfolio_values, 
                linewidth=2, label='Portefeuille')
        ax.axhline(y=report['initial_capital'], color='g', linestyle='--', 
                   alpha=0.5, label='Capital initial')
        ax.set_title(f'Valeur du Portefeuille ({self.ticker})', fontsize=14, fontweight='bold')
        ax.set_xlabel('Jours')
        ax.set_ylabel('Valeur ($)')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_file = f'reports/plots/portfolio_performance_{self.ticker}.png'
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"[CHECK] Graphique sauvegarde: {plot_file}")
        plt.close()


def main():
    """Point d'entree"""
    
    # Configuration
    TICKERS = ['AAPL']  # Ajouter plus de tickers si desire
    MODEL_TYPE = 'gradient_boosting'  # ou 'random_forest', 'neural_network'
    START_DATE = '2022-01-01'
    
    # Creer les repertoires
    os.makedirs('data', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # Lancer le pipeline
    for ticker in TICKERS:
        pipeline = TradingPipeline(ticker=ticker, model_type=MODEL_TYPE)
        pipeline.run(start_date=START_DATE)


if __name__ == "__main__":
    main()
