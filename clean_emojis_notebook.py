#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove emojis from notebook cells to avoid encoding issues"""

import json
import re

emoji_map = {
    '\U0001f4ca': '[STATS]',  # 📊
    '✅': '[OK]',          # ✅
    '⚠️': '[WARN]',  # ⚠️
    '❌': '[ERROR]',       # ❌
    '\U0001f914': '[THINK]',   # 🤔
    '\U0001f4d0': '[INFO]',    # 📐
    '\U0001f4cd': '[GRAPH]',   # 📍
    '\U0001f4e6': '[BOX]',     # 📦
    '⚠': '[WARN]',        # ⚠
    '\U0001f4ca': '[STATS]',   # 📊
    '\U0001f431': '[CAT]',     # 🐱
    '\U0001f4d6': '[BOOK]',    # 📖
}

# Carregar notebook
nb_path = 'notebooks/07_model_clustering_kmeans.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Remover emojis de todas as células
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']

        # Remover emojis comuns
        source = re.sub(r'[\U0001F300-\U0001F9FF]|\u26[A-F0-9]️?|☀-➿', '', source)

        # Converter de volta para lista
        cell['source'] = source.split('\n')[:-1] + [source.split('\n')[-1].rstrip('\n')] if source else []
        for i, line in enumerate(cell['source'][:-1]):
            cell['source'][i] = line + '\n'

# Salvar
with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("[OK] Emojis removidos do notebook")
