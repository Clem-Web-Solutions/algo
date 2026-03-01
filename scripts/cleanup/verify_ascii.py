#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verifier que tous les fichiers src sont en pur ASCII"""

import os

files_to_check = [
    'src/core/data_fetcher.py',
    'src/core/backtest_engine.py', 
    'src/core/trading_model.py',
    'src/core/config.py',
    'src/core/main.py',
    'src/analysis/advanced_analysis.py',
    'src/analysis/benchmark_comparison.py',
    'src/analysis/benchmark_improved.py',
    'src/analysis/feature_engineering.py',
    'src/analysis/model_comparison.py',
    'src/analysis/parameter_grid_search.py',
    'src/analysis/parameter_grid_search_v2.py',
    'src/analysis/parameter_optimization.py',
    'src/strategies/adaptive_strategy.py',
    'src/strategies/market_regime_detector.py'
]

print('[CHECK] Verification de l\'encodage ASCII:')
print('-' * 80)

non_ascii_files = []
total_replacements = 0

for file in files_to_check:
    if os.path.exists(file):
        with open(file, 'rb') as f:
            raw = f.read()
            try:
                raw.decode('ascii')
                print('[OK] {:<50} - 100 pct ASCII'.format(file))
            except UnicodeDecodeError as e:
                non_ascii_files.append(file)
                print('[ERROR] {:<50} - NON-ASCII detected'.format(file))
    else:
        print('[SKIP] {:<50} - Fichier non trouve'.format(file))

print('-' * 80)
print('[RESULT] Fichiers OK: {}/{}'.format(len(files_to_check) - len(non_ascii_files), len(files_to_check)))

if non_ascii_files:
    print('\n[WARNING] Fichiers avec caracteres non-ASCII:')
    for f in non_ascii_files:
        print('  - {}'.format(f))
else:
    print('\n[SUCCESS] Tous les fichiers sont 100% ASCII-compatible!')
