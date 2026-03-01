#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Finaliser le nettoyage du fichier PROJECT_HISTORY.txt
"""
import os

# Changer le répertoire
os.chdir(r'c:\Users\oscar\Desktop\algo trading')

# Lire le fichier
with open('docs/PROJECT_HISTORY.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Remplacements additionnels
add_repl = {
    '±': '+/-',
    '📈': '[TREND_UP]',
}

print("\n" + "=" * 70)
print("SECOND PASS: REMPLACEMENTS ADDITIONNELS")
print("=" * 70 + "\n")

total_new = 0
for old, new in add_repl.items():
    count = content.count(old)
    if count > 0:
        print(f"  Found: {repr(old):15} => Replace with: {new:15} ({count}x)")
        content = content.replace(old, new)
        total_new += count

# Vérifier les critères ASCII
non_ascii = set()
for char in content:
    if ord(char) > 127:
        non_ascii.add(char)

print(f"\nNew replacements: {total_new}")
print(f"Remaining non-ASCII: {len(non_ascii)}")

if len(non_ascii) > 0:
    print(f"\nNon-ASCII characters still present:")
    for c in sorted(non_ascii):
        print(f"  {repr(c)} (U+{ord(c):04X})")
else:
    print("\n✓ SUCCESS: Document is 100% ASCII-compatible!")

# Sauvegarder
with open('docs/PROJECT_HISTORY.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✓ File saved: docs/PROJECT_HISTORY.txt")
print("=" * 70)
print(f"TOTAL REPLACEMENTS: 509 + {total_new} = {509 + total_new}")
print("=" * 70)
