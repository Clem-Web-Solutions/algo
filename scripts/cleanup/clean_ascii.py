#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Clean all Python files to pure ASCII encoding"""

import os

files_to_clean = [
    'src/core/backtest_engine.py',
    'src/core/trading_model.py',
    'src/core/config.py',
    'src/analysis/advanced_analysis.py',
    'src/analysis/benchmark_comparison.py',
    'src/analysis/benchmark_improved.py',
    'src/analysis/feature_engineering.py',
    'src/analysis/model_comparison.py',
    'src/analysis/parameter_grid_search.py',
    'src/analysis/parameter_optimization.py',
    'src/strategies/adaptive_strategy.py',
    'src/strategies/market_regime_detector.py'
]

print('[START] Nettoyage complet UTF-8 -> ASCII')
print('-' * 80)

total_cleaned = 0

for file in files_to_clean:
    if not os.path.exists(file):
        print('[SKIP] {} - Non trouve'.format(file))
        continue
    
    try:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replacements
        replacements = {
            'Télécharger': 'Telecharger',
            'télécharger': 'telecharger',
            'données': 'donnees',
            'Données': 'Donnees',
            'données': 'donnees',
            'historique': 'historique',
            'début': 'debut',
            'fin': 'fin',
            'Modèle': 'Modele',
            'modèle': 'modele',
            'évaluation': 'evaluation',
            'Evaluation': 'Evaluation',
            'métriques': 'metriques',
            'Métriques': 'Metriques',
            'avancées': 'avancees',
            'Avancées': 'Avancees',
            'résumé': 'resume',
            'Résumé': 'Resume',
            'recommandations': 'recommendations',
            'optimisation': 'optimisation',
            'Optimisation': 'Optimisation',
            'résultats': 'resultats',
            'Résultats': 'Resultats',
            'sauvegardés': 'sauvegardes',
            'sauvegardé': 'sauvegarde',
            'Sauvegardé': 'Sauvegarde',
            'paramètres': 'parametres',
            'Paramètres': 'Parametres',
            'régime': 'regime',
            'Régime': 'Regime',
            'régimes': 'regimes',
            'Régimes': 'Regimes',
            'marché': 'marche',
            'Marché': 'Marche',
            'tâche': 'tache',
            'stragégies': 'strategies',
            'stratégies': 'strategies',
            'Stratégies': 'Strategies',
            'prédictions': 'predictions',
            'prédire': 'predire',
            'gérer': 'gerer',
            'Aucune': 'Aucune',
            'aucune': 'aucune',
            'rééxecution': 'reexecution',
            'confiance': 'confiance',
            'confiance': 'confiance',
            'Confiance': 'Confiance',
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # Test ASCII
        content.encode('ascii')
        
        # Write
        with open(file, 'w', encoding='ascii') as f:
            f.write(content)
        
        print('[OK] {}'.format(file))
        total_cleaned += 1
        
    except Exception as e:
        print('[ERROR] {} - {}'.format(file, str(e)))

print('-' * 80)
print('[RESULT] {} fichiers nettoyes sur {}'.format(total_cleaned, len(files_to_clean)))
