#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vérification finale et remplacements des caractères non-ASCII restants
"""

import sys
import os

os.chdir(r"c:\Users\oscar\Desktop\algo trading")

with open('docs/PROJECT_HISTORY.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacements finaux
additional_replacements = {
    '±': '+/-',
    '📈': '[TREND_UP]',
}

print("=" * 70)
print("REMPLACEMENTS ADDITIONNELS")
print("=" * 70 + "\n")

total_add = 0
for old, new in additional_replacements.items():
    count = content.count(old)
    if count > 0:
        print(f"  {repr(old):15} => {new:15} : {count:3} x")
        content = content.replace(old, new)
        total_add += count

# Vérifier les caractères non-ASCII
non_ascii_chars = set()
for char in content:
    if ord(char) > 127:
        non_ascii_chars.add(char)

print(f"\nRemplacements effectués: {total_add}")
print(f"Caractères non-ASCII restants: {len(non_ascii_chars)}")

if len(non_ascii_chars) == 0:
    print("\n" + "=" * 70)
    print("✓ SUCCES: Le document est 100% ASCII-compatible!")
    print("=" * 70)
else:
    print(f"\nCaractères non-ASCII restants:")
    for char in sorted(non_ascii_chars):
        print(f"  {repr(char)} (U+{ord(char):04X})")

# Sauvegarder
with open('docs/PROJECT_HISTORY.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✓ Fichier finalisé: docs/PROJECT_HISTORY.txt")
print(f"\nTOTAL REMPLACEMENTS DEFINITIF: 509 + {total_add} = {509 + total_add}")
print("=" * 70)
