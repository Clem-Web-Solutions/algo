#!/usr/bin/env python
"""Test final - Verifier que tous les modules se chargent correctement"""

import sys
import os

os.chdir('c:\\Users\\oscar\\Desktop\\algo trading')
sys.path.insert(0, 'src/core')
sys.path.insert(0, 'src/analysis')
sys.path.insert(0, 'src/strategies')

print('[TEST] Chargement des modules Python')
print('-' * 80)

modules_to_test = [
    ('src.core.data_fetcher', 'DataFetcher'),
    ('src.core.backtest_engine', 'BacktestEngine'),
    ('src.core.trading_model', 'TradingModel'),
    ('src.core.config', 'TICKERS'),
    ('src.analysis.advanced_analysis', 'AdvancedAnalysis'),
    ('src.analysis.feature_engineering', 'FeatureEngineering'),
    ('src.strategies.adaptive_strategy', 'AdaptiveStrategy'),
    ('src.strategies.market_regime_detector', 'MarketRegimeDetector'),
]

success_count = 0
for module_name, class_name in modules_to_test:
    try:
        module = __import__(module_name, fromlist=[class_name])
        getattr(module, class_name)
        print('[OK] {} - {}'.format(module_name, class_name))
        success_count += 1
    except Exception as e:
        print('[ERROR] {} - {}'.format(module_name, str(e)[:60]))

print('-' * 80)
print('[RESULT] {}/{} modules loadable'.format(success_count, len(modules_to_test)))

if success_count == len(modules_to_test):
    print('\n[SUCCESS] Tous les modules se chargent correctement!')
else:
    print('\n[WARNING] Certains modules ont des problemes')
