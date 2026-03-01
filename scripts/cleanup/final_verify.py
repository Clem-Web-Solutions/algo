#!/usr/bin/env python
# Verification ASCII finale

import os
import sys

os.chdir('c:\\Users\\oscar\\Desktop\\algo trading')

files = [
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

print('[CHECK] Verification ASCII finale')
print('-' * 80)

ok_count = 0
error_files = []

for f in files:
    try:
        with open(f, 'rb') as fd:
            data = fd.read()
            try:
                data.decode('ascii')
                print('[OK] {}'.format(f))
                ok_count += 1
            except UnicodeDecodeError as e:
                error_files.append(f)
                print('[ERROR] {} - Non-ASCII at byte {}'.format(f, e.start))
    except FileNotFoundError:
        print('[SKIP] {} - Not found'.format(f))

print('-' * 80)
print('[RESULT] OK: {}/{}'.format(ok_count, len(files)))

if error_files:
    print('\n[WARNINGS] Non-ASCII files:')
    for f in error_files:
        print('  - {}'.format(f))
else:
    print('\n[SUCCESS] All files are 100% ASCII!')
    sys.exit(0)

sys.exit(1)
