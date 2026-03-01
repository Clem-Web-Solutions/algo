#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nettoyer PROJECT_HISTORY.txt: remplacer tous les emojis et accents français
pour rendre le document 100% ASCII-compatible
"""

with open('docs/PROJECT_HISTORY.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Dictionnaire complet des remplacements
replacements = {
    # Emojis
    '🎯': '[TARGET]',
    '⚡': '[BOLT]',
    '✅': '[CHECK]',
    '⭐': '[STAR]',
    '8️⃣': '[EIGHT]',
    '🟠': '[ORANGE]',
    '🟡': '[YELLOW]',
    '🟢': '[GREEN]',
    '🔴': '[RED]',
    '📊': '[CHART]',
    '📋': '[LIST]',
    '📉': '[CHART_DOWN]',
    '🔍': '[SEARCH]',
    '⚠️': '[WARNING]',
    '🎓': '[GRADUATION]',
    '💡': '[LIGHTBULB]',
    '🏆': '[TROPHY]',
    '🚀': '[ROCKET]',
    '🔧': '[WRENCH]',
    '🐻': '[BEAR]',
    # Flèches/caractères spéciaux
    '→': '->',
    # Accents minuscules
    'é': 'e',
    'è': 'e',
    'ê': 'e',
    'à': 'a',
    'î': 'i',
    'ô': 'o',
    'ù': 'u',
    'ç': 'c',
    # Accents majuscules
    'Ç': 'C',
    'É': 'E',
    'È': 'E',
    'Ê': 'E',
    'Ë': 'E',
    'À': 'A',
    'Î': 'I',
    'Ô': 'O',
    'Ù': 'U',
}

# Compter et afficher les remplacements avant
print("=" * 70)
print("ANALYSE DES CARACTERES NON-ASCII")
print("=" * 70)
print("\nCARACTERES À REMPLACER:\n")

total_before = 0
replacement_details = []

for old, new in replacements.items():
    count = content.count(old)
    if count > 0:
        replacement_details.append((old, new, count))
        print(f'  {repr(old):15} => {new:15} : {count:3} x')
        total_before += count

print(f"\n{"-"*70}")
print(f"TOTAL CARACTERES À REMPLACER: {total_before}")
print(f"{"-"*70}\n")

# Effectuer les remplacements
new_content = content
actual_replacements = 0

for old, new in replacements.items():
    count = new_content.count(old)
    if count > 0:
        new_content = new_content.replace(old, new)
        actual_replacements += count

# Vérifier qu'il ne reste pas de caractères non-ASCII (> 127)
import string
non_ascii_found = []
for i, char in enumerate(new_content):
    if ord(char) > 127:
        non_ascii_found.append((char, ord(char), i))

# Afficher les résultats
print("RESULTATS:\n")
print(f"✓ Remplacements effectués: {actual_replacements}")
print(f"✓ Caractères non-ASCII restants: {len(non_ascii_found)}")

if non_ascii_found:
    print("\nCaractères non-ASCII restants (premiers 10):")
    for char, code, pos in non_ascii_found[:10]:
        print(f"  Char: {repr(char)}, Code: {code} (U+{code:04X}), Position: {pos}")
else:
    print("\n✓ Le document est 100% ASCII-compatible!")

# Sauvegarder le fichier
with open('docs/PROJECT_HISTORY.txt', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("\n" + "=" * 70)
print("✓ Fichier sauvegardé: docs/PROJECT_HISTORY.txt")
print("=" * 70)

# Rapport final
print(f"\nRAPPORT FINAL:")
print(f"  Emojis remplacés: {sum(1 for o, n, c in replacement_details if '[' in n)}")
print(f"  Accents supprimés: {sum(1 for o, n, c in replacement_details if '[' not in n and o not in ['→'])}")
print(f"  Tirets spéciaux: {sum(1 for o, n, c in replacement_details if o == '→')}")
print(f"  TOTAL: {actual_replacements} remplacements")
