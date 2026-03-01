"""
Test du modèle Neural Network sur plusieurs tickers
Compare la performance du Neural Network sur AAPL, MSFT, GOOGL, TSLA
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from data_fetcher import DataFetcher
from feature_engineering import FeatureEngineering
from trading_model import TradingModel
from backtest_engine import BacktestEngine


class MultiTickerTester:
    """Teste le modèle Neural Network sur plusieurs tickers"""
    
    def __init__(self, tickers=['AAPL', 'MSFT', 'GOOGL', 'TSLA']):
        self.tickers = tickers
        self.results = {}
        self.backtest_results = {}
    
    def run_all_tickers(self, start_date='2022-01-01', model_type='neural_network'):
        """Teste le modèle sur tous les tickers"""
        print("\n" + "="*80)
        print(f"🌍 TEST MULTI-TICKERS - {model_type.replace('_', ' ').upper()}")
        print("="*80)
        
        for ticker in self.tickers:
            print(f"\n\n{'─'*80}")
            print(f"📈 Traitement de {ticker}...")
            print(f"{'─'*80}")
            
            self._test_ticker(ticker, start_date, model_type)
        
        # Générer le rapport
        print(f"\n\n{'─'*80}")
        print(f"📊 GÉNÉRATION DU RAPPORT COMPARATIF")
        print(f"{'─'*80}")
        self._generate_comparison_report()
        
        print("\n✅ Analyse complétée!")
    
    def _test_ticker(self, ticker, start_date, model_type):
        """Teste un ticker spécifique"""
        try:
            # 1. Télécharger les données
            print(f"\n[1/4] Téléchargement des données {ticker}...")
            fetcher = DataFetcher()
            data = fetcher.fetch_stock_data(ticker, start_date=start_date)
            print(f"     ✓ {len(data)} jours de données")
            
            # 2. Créer les features
            print(f"[2/4] Création des indicateurs...")
            fe = FeatureEngineering()
            data = fe.add_technical_indicators(data)
            data['Target'] = fe.create_target_variable(data, prediction_window=5)
            
            # 3. Préparer et entraîner
            print(f"[3/4] Entraînement du modèle {model_type}...")
            X_train, X_test, y_train, y_test, scaler = fe.prepare_training_data(data)
            
            model = TradingModel(model_type=model_type)
            cv_scores = model.train(X_train, y_train)
            
            # Évaluer
            metrics = model.evaluate(X_test, y_test)
            self.results[ticker] = {
                'metrics': metrics,
                'cv_score': cv_scores.mean()
            }
            
            print(f"     ✓ Accuracy: {metrics['accuracy']:.4f}")
            print(f"     ✓ F1-Score: {metrics['f1']:.4f}")
            print(f"     ✓ ROC-AUC: {metrics['roc_auc']:.4f}")
            
            # 4. Backtest
            print(f"[4/4] Backtesting de la stratégie...")
            predictions = model.predict(X_test)
            test_dates = X_test.index
            
            engine = BacktestEngine(initial_capital=10000, position_size_pct=0.95,
                                   stop_loss_pct=-2.0, take_profit_pct=5.0, use_trend_filter=True)
            report = engine.run_backtest(data, model, X_test, test_dates, predictions)
            
            self.backtest_results[ticker] = report
            
            print(f"     ✓ Rendement: {report['total_return_pct']:.2f}%")
            print(f"     ✓ Taux de réussite: {report['win_rate']:.2f}%")
            print(f"     ✓ Nombre de trades: {report['total_trades']}")
            
        except Exception as e:
            print(f"     ❌ Erreur: {str(e)}")
            self.results[ticker] = None
            self.backtest_results[ticker] = None
    
    def _generate_comparison_report(self):
        """Génère un rapport comparatif des tickers"""
        # Créer un DataFrame de comparaison
        comparison_data = []
        
        for ticker in self.tickers:
            if ticker not in self.results or self.results[ticker] is None:
                continue
            
            metrics = self.results[ticker]['metrics']
            backtest = self.backtest_results[ticker]
            
            row = {
                'Ticker': ticker,
                'Accuracy': f"{metrics['accuracy']:.4f}",
                'Precision': f"{metrics['precision']:.4f}",
                'Recall': f"{metrics['recall']:.4f}",
                'F1-Score': f"{metrics['f1']:.4f}",
                'ROC-AUC': f"{metrics['roc_auc']:.4f}",
                'CV Score': f"{self.results[ticker]['cv_score']:.4f}",
                'Rendement': f"{backtest['total_return_pct']:.2f}%",
                'Win Rate': f"{backtest['win_rate']:.2f}%",
                'Trades': backtest['total_trades'],
                'Drawdown': f"{backtest['max_drawdown']:.2f}%"
            }
            comparison_data.append(row)
        
        df_comparison = pd.DataFrame(comparison_data)
        
        # Afficher le tableau
        print("\n" + "="*120)
        print("📊 RAPPORT COMPARATIF MULTI-TICKERS")
        print("="*120)
        print(df_comparison.to_string(index=False))
        print("="*120)
        
        # Sauvegarder le rapport
        self._save_text_report(df_comparison)
        
        # Générer les graphiques
        self._create_comparison_plots()
    
    def _save_text_report(self, df_comparison):
        """Sauvegarde un rapport texte"""
        filename = f'reports/multi_ticker_report_neural_network_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*120 + "\n")
            f.write(f"RAPPORT DE TEST MULTI-TICKERS - NEURAL NETWORK\n")
            f.write("="*120 + "\n\n")
            
            f.write(f"Date rapport: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tickers testés: {', '.join(self.tickers)}\n")
            f.write(f"Modèle: Neural Network (128, 64, 32 layers)\n\n")
            
            f.write("-"*120 + "\n")
            f.write("TABLEAU COMPARATIF\n")
            f.write("-"*120 + "\n")
            f.write(df_comparison.to_string(index=False) + "\n\n")
            
            f.write("-"*120 + "\n")
            f.write("ANALYSE DÉTAILLÉE PAR TICKER\n")
            f.write("-"*120 + "\n\n")
            
            for ticker in self.tickers:
                if ticker not in self.results or self.results[ticker] is None:
                    f.write(f"\n{ticker}: ❌ Erreur lors du traitement\n")
                    continue
                
                metrics = self.results[ticker]['metrics']
                backtest = self.backtest_results[ticker]
                
                f.write(f"\n{ticker}\n")
                f.write("-" * 40 + "\n")
                f.write("Métriques de Validation:\n")
                f.write(f"  - Accuracy: {metrics['accuracy']:.4f}\n")
                f.write(f"  - Precision: {metrics['precision']:.4f}\n")
                f.write(f"  - Recall: {metrics['recall']:.4f}\n")
                f.write(f"  - F1-Score: {metrics['f1']:.4f}\n")
                f.write(f"  - ROC-AUC: {metrics['roc_auc']:.4f}\n")
                f.write(f"  - CV Score: {self.results[ticker]['cv_score']:.4f}\n\n")
                
                f.write("Résultats Backtest:\n")
                f.write(f"  - Période: {backtest['start_date']} -> {backtest['end_date']}\n")
                f.write(f"  - Rendement total: {backtest['total_return_pct']:.2f}%\n")
                f.write(f"  - Capital initial: ${backtest['initial_capital']:.2f}\n")
                f.write(f"  - Valeur finale: ${backtest['final_value']:.2f}\n")
                f.write(f"  - Taux de réussite: {backtest['win_rate']:.2f}%\n")
                f.write(f"  - Nombre de trades: {backtest['total_trades']}\n")
                f.write(f"  - Achats: {backtest['buy_trades']}\n")
                f.write(f"  - Ventes: {backtest['sell_trades']}\n")
                f.write(f"  - Profit moyen: ${backtest['avg_profit']:.2f}\n")
                f.write(f"  - Perte moyenne: ${backtest['avg_loss']:.2f}\n")
                f.write(f"  - Drawdown max: {backtest['max_drawdown']:.2f}%\n")
        
        print(f"\n✅ Rapport sauvegardé: {filename}")
    
    def _create_comparison_plots(self):
        """Crée les graphiques comparatifs"""
        import os
        os.makedirs('reports/plots', exist_ok=True)
        
        valid_tickers = [t for t in self.tickers if t in self.results and self.results[t] is not None]
        
        # 1. Comparaison des métriques
        fig, axes = plt.subplots(2, 3, figsize=(18, 10))
        fig.suptitle('Comparaison des Modèles par Ticker (Neural Network)', fontsize=16, fontweight='bold')
        
        metrics_names = ['Accuracy', 'Precision', 'Recall', 'F1-Score', 'ROC-AUC']
        metrics_keys = ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']
        
        for idx, (metric_name, metric_key) in enumerate(zip(metrics_names, metrics_keys)):
            ax = axes[idx // 3, idx % 3]
            
            values = [self.results[ticker]['metrics'][metric_key] for ticker in valid_tickers]
            
            bars = ax.bar(valid_tickers, values, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(valid_tickers)], 
                          alpha=0.7, edgecolor='black')
            ax.set_ylim([0, 1])
            ax.set_title(metric_name, fontweight='bold')
            ax.set_ylabel('Score')
            ax.grid(axis='y', alpha=0.3)
            
            # Ajouter les valeurs sur les barres
            for bar, value in zip(bars, values):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                       f'{value:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        # Retirer le dernier subplot vide
        axes[1, 2].axis('off')
        
        plt.tight_layout()
        plot_file = f'reports/plots/multi_ticker_metrics_neural_network.png'
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"✅ Graphique sauvegardé: {plot_file}")
        plt.close()
        
        # 2. Comparaison des résultats de backtest
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Résultats Backtest par Ticker (Neural Network)', fontsize=16, fontweight='bold')
        
        # Rendement
        ax = axes[0, 0]
        returns = [self.backtest_results[ticker]['total_return_pct'] for ticker in valid_tickers]
        colors = ['green' if r > 0 else 'red' for r in returns]
        bars = ax.bar(valid_tickers, returns, color=colors, alpha=0.7, edgecolor='black')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title('Rendement Total (%)', fontweight='bold')
        ax.set_ylabel('Rendement (%)')
        for bar, value in zip(bars, returns):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (0.1 if value > 0 else -0.3),
                   f'{value:.2f}%', ha='center', va='bottom' if value > 0 else 'top', fontsize=10, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Taux de réussite
        ax = axes[0, 1]
        win_rates = [self.backtest_results[ticker]['win_rate'] for ticker in valid_tickers]
        bars = ax.bar(valid_tickers, win_rates, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(valid_tickers)], 
                      alpha=0.7, edgecolor='black')
        ax.set_ylim([0, 100])
        ax.set_title('Taux de Réussite (%)', fontweight='bold')
        ax.set_ylabel('Taux (%)')
        for bar, value in zip(bars, win_rates):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                   f'{value:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Nombre de trades
        ax = axes[1, 0]
        trades = [self.backtest_results[ticker]['total_trades'] for ticker in valid_tickers]
        bars = ax.bar(valid_tickers, trades, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(valid_tickers)], 
                      alpha=0.7, edgecolor='black')
        ax.set_title('Nombre de Trades', fontweight='bold')
        ax.set_ylabel('Nombre')
        for bar, value in zip(bars, trades):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                   f'{int(value)}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Drawdown max
        ax = axes[1, 1]
        drawdowns = [abs(self.backtest_results[ticker]['max_drawdown']) for ticker in valid_tickers]
        bars = ax.bar(valid_tickers, drawdowns, color=['#d62728', '#d62728', '#d62728', '#d62728'][:len(valid_tickers)], 
                      alpha=0.7, edgecolor='black')
        ax.set_title('Drawdown Maximum (%)', fontweight='bold')
        ax.set_ylabel('Drawdown (%)')
        for bar, value in zip(bars, drawdowns):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                   f'{value:.2f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plot_file = f'reports/plots/multi_ticker_backtest_neural_network.png'
        plt.savefig(plot_file, dpi=150, bbox_inches='tight')
        print(f"✅ Graphique sauvegardé: {plot_file}")
        plt.close()


def main():
    """Point d'entrée"""
    tester = MultiTickerTester(tickers=['AAPL', 'MSFT', 'GOOGL', 'TSLA'])
    tester.run_all_tickers(start_date='2022-01-01', model_type='neural_network')


if __name__ == "__main__":
    main()
