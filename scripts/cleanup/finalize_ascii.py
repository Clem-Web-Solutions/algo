#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finaliser le nettoyage: remplacer les 4 caractères non-ASCII restants
"""

# Lire le fichier
with open('docs/PROJECT_HISTORY.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacements supplémentaires
additional_replacements = {
    '±': '+/-',
    '📈': '[TREND_UP]',
}

print("\nREMPLACEMENTS ADDITIONNELS:\n")
total_add = 0

for old, new in additional_replacements.items():
    count = content.count(old)
    if count > 0:
        print(f"  {repr(old):15} => {new:15} : {count:3} x")
        content = content.replace(old, new)
        total_add += count

# Vérifier qu'il ne reste pas de caractères non-ASCII
non_ascii_found = []
for i, char in enumerate(content):
    if ord(char) > 127:
        non_ascii_found.append((char, ord(char), i))

print(f"\nRemplacements additionnels: {total_add}")
print(f"Caractères non-ASCII restants: {len(non_ascii_found)}")

if non_ascii_found:
    print("\nCaractères non-ASCII encore présents:")
    for char, code, pos in non_ascii_found[:10]:
        print(f"  {repr(char)} (U+{code:04X})")
else:
    print("\n✓ Le document est MAINTENANT 100% ASCII-compatible!")

# Sauvegarder
with open('docs/PROJECT_HISTORY.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓ Fichier finalisé!")
print(f"TOTAL REMPLACEMENTS DÉFINITIF: 509 + {total_add} = {509 + total_add}")
