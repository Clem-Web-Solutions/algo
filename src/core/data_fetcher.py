"""
Module pour telecharger les donnees reelles du marche financier
"""
import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

class DataFetcher:
    """Récupère les données réelles de marché"""
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
    
    def fetch_stock_data(self, ticker, start_date=None, end_date=None, interval='1d'):
        """
        Telecharge les donnees historiques d'une action
        
        Args:
            ticker: Code de l'action (ex: 'AAPL', 'MSFT', 'EURUSD=X')
            start_date: Date de debut (format: 'YYYY-MM-DD')
            end_date: Date de fin (format: 'YYYY-MM-DD')
            interval: Intervalle temporel ('1m', '5m', '15m', '1h', '1d')
        
        Returns:
            DataFrame avec les donnees OHLCV
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if start_date is None:
            # Par defaut: 5 ans d'historique
            start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y-%m-%d')
        
        print(f"[CHART] Telecharge de {ticker} du {start_date} au {end_date}...")
        
        try:
            data = yf.download(ticker, start=start_date, end=end_date, interval=interval, progress=False)
            
            # Verifier que nous avons bien des donnees
            if data.empty:
                raise ValueError(f"Aucune donnee trouvee pour {ticker}")
            
            # Nettoyer les donnees
            data = self._clean_data(data)
            
            # Sauvegarder localement
            filepath = os.path.join(self.data_dir, f'{ticker}_{start_date}_{end_date}.csv')
            data.to_csv(filepath)
            print(f"[CHECK] {len(data)} jours de donnees recuperes et sauvegardes")
            
            return data
            
        except Exception as e:
            print(f"❌ Erreur: {str(e)}")
            raise
    
    def _clean_data(self, data):
        """Nettoie et valide les donnees"""
        # Flattir les colonnes multi-niveaux (yfinance cree parfois des MultiIndex)
        if isinstance(data.columns, pd.MultiIndex):
            # Si colonnes multi-niveaux, garder le premier niveau
            data.columns = data.columns.get_level_values(0)
        
        # Supprimer les lignes avec NaN
        data = data.dropna()
        
        # Verifier qu'on a au least les colonnes essentielles
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in data.columns:
                raise ValueError(f"Colonne manquante: {col}")
        
        # S'assurer que le volume n'est pas vide
        data = data[data['Volume'] > 0]
        
        return data
    
    def fetch_multiple(self, tickers, start_date=None, end_date=None):
        """Telecharge les donnees pour plusieurs actions"""
        results = {}
        for ticker in tickers:
            try:
                results[ticker] = self.fetch_stock_data(ticker, start_date, end_date)
            except Exception as e:
                print(f"[WARNING] Erreur pour {ticker}: {str(e)}")
        
        return results


if __name__ == "__main__":
    # Exemple d'utilisation
    fetcher = DataFetcher()
    
    # Télécharger des données réelles
    print("=" * 60)
    print("TÉLÉCHARGEMENT DES DONNÉES DE MARCHÉ")
    print("=" * 60)
    
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    for ticker in tickers:
        try:
            data = fetcher.fetch_stock_data(ticker, start_date='2022-01-01')
            print(f"\n{ticker}:")
            print(data.head())
        except Exception as e:
            print(f"Erreur: {e}")
