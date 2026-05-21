#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir o notebook 07 — implementar Feature Selection CAUSA/EFEITO
e inserir visualizações para melhor entendimento dos dados.
"""

import json
import copy
import sys
import os

# Força UTF-8 output no Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Carregar notebook
nb_path = 'notebooks/07_model_clustering_kmeans.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"[OK] Notebook carregado: {len(nb['cells'])} células")

# ============================================================================
# CELL 3B (NOVA): EDA + FEATURE SELECTION
# ============================================================================
cell_3b = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# ===== [3b] EDA: VISUALIZAÇÃO DOS DADOS ANTES DE QUALQUER TRANSFORMAÇÃO =====\n",
        "import matplotlib.pyplot as plt\n",
        "import seaborn as sns\n",
        "\n",
        "# ===== DEFINIR FEATURES: CAUSA vs EFEITO =====\n",
        "# CAUSA: Features de ENTRADA (como o incidente chegou)\n",
        "cause_cols = [\n",
        "    'prioridade_num', 'grupo_designado', 'categoria', 'subcategoria', 'produto',\n",
        "    'hora_abertura', 'turno_abertura', 'dia_semana_num', 'fora_horario_comercial',\n",
        "    'abriu_fim_de_semana', 'mes_abertura', 'trimestre', 'possui_pai', 'triagem_incompleta'\n",
        "]\n",
        "\n",
        "# EFEITO: Features de SAÍDA (resultado da resolução) — EXCLUIR do treino de clustering\n",
        "effect_cols = [\n",
        "    'duracao_horas', 'horas_ate_resolucao', 'foi_resolvido', 'excedeu_tempo_esperado',\n",
        "    'fechado_sem_tecnico', 'target_risco_sla', 'score_risco_operacional'\n",
        "]\n",
        "\n",
        "# EXCLUIR: Colunas inúteis, NULL placeholders, ou redundantes\n",
        "exclude_cols = [\n",
        "    'incident_id', 'cluster', 'data_abertura',\n",
        "    'duracao_horas_scaled', 'cluster_id',  # NULL placeholders\n",
        "    'is_filho_de_problema'  # Redundante a 'possui_pai'\n",
        "]\n",
        "\n",
        "print(f'📊 ESTRUTURA DE FEATURES:')\n",
        "print(f'   ✅ CAUSA (incluir no treino): {len(cause_cols)} colunas')\n",
        "print(f'   ⚠️  EFEITO (usar para interpretar): {len(effect_cols)} colunas')\n",
        "print(f'   ❌ EXCLUIR (data leakage, NULL, redundante): {len(exclude_cols)} colunas')\n",
        "print(f'\\n   Total colunas dataset: {len(df.columns)}')\n",
        "\n",
        "# ===== CRIAR EDA COM 6 GRÁFICOS =====\n",
        "fig, axes = plt.subplots(2, 3, figsize=(18, 10))\n",
        "fig.suptitle('EDA: Análise de Features ANTES de Transformação', fontsize=14, fontweight='bold')\n",
        "\n",
        "# [1] Cardinalidade das colunas categóricas\n",
        "cat_cols_all = df.select_dtypes(include=['object']).columns.tolist()\n",
        "cardinality = {col: df[col].nunique() for col in cat_cols_all}\n",
        "cardinality_sorted = dict(sorted(cardinality.items(), key=lambda x: x[1], reverse=True))\n",
        "axes[0, 0].barh(list(cardinality_sorted.keys()), list(cardinality_sorted.values()), color='steelblue')\n",
        "axes[0, 0].set_xlabel('Número de Valores Únicos')\n",
        "axes[0, 0].set_title('1. Cardinalidade — Colunas Categóricas')\n",
        "axes[0, 0].grid(axis='x', alpha=0.3)\n",
        "for i, (col, val) in enumerate(cardinality_sorted.items()):\n",
        "    strategy = 'OHE' if val <= 20 else 'Freq.Enc'\n",
        "    axes[0, 0].text(val, i, f' {val} ({strategy})', va='center', fontweight='bold')\n",
        "\n",
        "# [2] Distribuição de features numéricas CAUSA (seleção)\n",
        "cause_numeric = [c for c in cause_cols if c in df.columns and df[c].dtype in ['int64', 'float64']]\n",
        "sample_cause = cause_numeric[:4] if len(cause_numeric) >= 4 else cause_numeric\n",
        "df[sample_cause].hist(ax=axes[0, 1], bins=30, color='green', alpha=0.7, edgecolor='black')\n",
        "axes[0, 1].set_title('2. Distribuição — Features CAUSA Numéricas (amostra)')\n",
        "axes[0, 1].grid(alpha=0.3)\n",
        "\n",
        "# [3] Correlação entre features CAUSA numéricas\n",
        "if len(cause_numeric) > 1:\n",
        "    corr_matrix = df[cause_numeric].corr()\n",
        "    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, \n",
        "                ax=axes[0, 2], cbar_kws={'label': 'Correlação'})\n",
        "    axes[0, 2].set_title('3. Correlação — Features CAUSA Numéricas')\n",
        "else:\n",
        "    axes[0, 2].text(0.5, 0.5, 'Sem features numéricos suficientes', \n",
        "                    ha='center', va='center', fontsize=12)\n",
        "    axes[0, 2].set_title('3. Correlação')\n",
        "\n",
        "# [4] Proporção de valores NULL por coluna\n",
        "null_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)\n",
        "null_pct = null_pct[null_pct > 0]  # Apenas colunas com NULLs\n",
        "if len(null_pct) > 0:\n",
        "    axes[1, 0].barh(null_pct.index, null_pct.values, color='coral')\n",
        "    axes[1, 0].set_xlabel('% de Valores NULL')\n",
        "    axes[1, 0].set_title('4. Valores NULL — Colunas Afetadas')\n",
        "    axes[1, 0].grid(axis='x', alpha=0.3)\n",
        "else:\n",
        "    axes[1, 0].text(0.5, 0.5, 'Nenhuma coluna com NULLs', ha='center', va='center', fontsize=12)\n",
        "    axes[1, 0].set_title('4. Valores NULL')\n",
        "\n",
        "# [5] Distribuição de 'categoria' (principal baixa-cardinalidade)\n",
        "if 'categoria' in df.columns:\n",
        "    categoria_dist = df['categoria'].value_counts().head(15)\n",
        "    axes[1, 1].barh(categoria_dist.index, categoria_dist.values, color='mediumseagreen')\n",
        "    axes[1, 1].set_xlabel('Contagem')\n",
        "    axes[1, 1].set_title('5. Top-15 Categorias — (Usar OHE)')\n",
        "    axes[1, 1].grid(axis='x', alpha=0.3)\n",
        "else:\n",
        "    axes[1, 1].text(0.5, 0.5, 'Coluna categoria não disponível', ha='center', va='center')\n",
        "    axes[1, 1].set_title('5. Categorias')\n",
        "\n",
        "# [6] Resumo de Features: CAUSA vs EFEITO vs EXCLUIR\n",
        "axes[1, 2].axis('off')\n",
        "summary_text = f'''RESUMO DE FEATURES:\n\n\n",
        "✅ CAUSA (incluir): {len(cause_cols)}\n",
        "   Objetivo: Perfil de entrada\n",
        "   Exemplos: prioridade, grupo,\n",
        "             hora, turno, categoria\n\n\n",
        "⚠️  EFEITO (interpretar):{len(effect_cols)}\n",
        "   Objetivo: Entender clusters\n",
        "   Exemplos: duracao, foi_resolvido,\n",
        "             excedeu_tempo_esperado\n\n\n",
        "❌ EXCLUIR: {len(exclude_cols)}\n",
        "   Razão: NULL, data leakage,\n",
        "          redundância'''\n",
        "axes[1, 2].text(0.05, 0.95, summary_text, transform=axes[1, 2].transAxes,\n",
        "                fontsize=11, verticalalignment='top', fontfamily='monospace',\n",
        "                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))\n",
        "axes[1, 2].set_title('6. Estratégia de Feature Selection', fontweight='bold')\n",
        "\n",
        "plt.tight_layout()\n",
        "eda_path = os.path.join(Path(r'D:\\Projetos\\AWS_Portifolio\\Projeto aws\\data\\ml\\kmeans'), 'eda_feature_selection.png')\n",
        "Path(eda_path).parent.mkdir(parents=True, exist_ok=True)\n",
        "fig.savefig(eda_path, dpi=100, bbox_inches='tight')\n",
        "plt.close()\n",
        "\n",
        "print(f'\\n✅ EDA salva em: {eda_path}')\n",
        "print(f'\\n📋 Features a INCLUIR (CAUSA):' + '\\n   ' + '\\n   '.join(cause_cols))\n"
    ]
}

# ============================================================================
# REWRITE CELL 4: Feature Engineering CAUSA/EFEITO + Encoding Otimizado
# ============================================================================
cell_4_new = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# ===== [4] FEATURE ENGINEERING: SELEÇÃO CAUSA + ENCODING OTIMIZADO =====\n",
        "from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder\n",
        "from sklearn.decomposition import PCA\n",
        "\n",
        "print('\\n🔧 FEATURE ENGINEERING: CAUSA + ENCODING OTIMIZADO')\n",
        "\n",
        "# ===== [4.1] OUTLIER REMOVAL (OR LÓGICO) =====\n",
        "numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()\n",
        "numeric_cols = [c for c in numeric_cols if c not in ['incident_id', 'cluster', 'data_abertura']]\n",
        "\n",
        "print(f'\\n📊 Dataset Original: {len(df):,} incidentes')\n",
        "print(f'   Colunas numéricas para outlier detection: {len(numeric_cols)}')\n",
        "\n",
        "# Calcular quantas colunas são outlier por linha (estratégia OR)\n",
        "outlier_counts = pd.DataFrame(index=df.index)\n",
        "for col in numeric_cols:\n",
        "    Q1 = df[col].quantile(0.25)\n",
        "    Q3 = df[col].quantile(0.75)\n",
        "    IQR = Q3 - Q1\n",
        "    lower = Q1 - 1.5 * IQR\n",
        "    upper = Q3 + 1.5 * IQR\n",
        "    outlier_counts[col] = ~((df[col] >= lower) & (df[col] <= upper))\n",
        "\n",
        "outlier_total_per_row = outlier_counts.sum(axis=1)\n",
        "max_outliers_allowed = len(numeric_cols) * 0.5\n",
        "outlier_mask = outlier_total_per_row <= max_outliers_allowed\n",
        "\n",
        "df_clean = df[outlier_mask].copy()\n",
        "n_removed = len(df) - len(df_clean)\n",
        "\n",
        "print(f'\\n🔍 Outlier Detection (IQR — OR lógico):' + \n",
        "      f'\\n   Removidos: {n_removed:,} incidentes ({n_removed/len(df)*100:.2f}%)' +\n",
        "      f'\\n   Mantidos: {len(df_clean):,} incidentes ({len(df_clean)/len(df)*100:.2f}%)')\n",
        "\n",
        "# ===== [4.2] SELECIONAR APENAS FEATURES CAUSA =====\n",
        "cause_cols = [\n",
        "    'prioridade_num', 'grupo_designado', 'categoria', 'subcategoria', 'produto',\n",
        "    'hora_abertura', 'turno_abertura', 'dia_semana_num', 'fora_horario_comercial',\n",
        "    'abriu_fim_de_semana', 'mes_abertura', 'trimestre', 'possui_pai', 'triagem_incompleta'\n",
        "]\n",
        "\n",
        "# Verificar quais existem no dataframe\n",
        "cause_cols_valid = [c for c in cause_cols if c in df_clean.columns]\n",
        "print(f'\\n✅ Features CAUSA válidas: {len(cause_cols_valid)} (original: {len(cause_cols)})')\n",
        "print(f'   {cause_cols_valid}')\n",
        "\n",
        "df_features = df_clean[cause_cols_valid].copy()\n",
        "\n",
        "# ===== [4.3] ENCODING CÍCLICO PARA TEMPORAIS =====\n",
        "print(f'\\n🔄 Encoding Cíclico para Features Temporais...')\n",
        "temporal_cyclic = {\n",
        "    'hora_abertura': 24,    # Hora 23 ≈ Hora 0\n",
        "    'dia_semana_num': 7,    # Domingo ≈ Sábado\n",
        "    'mes_abertura': 12      # Dezembro ≈ Janeiro\n",
        "}\n",
        "\n",
        "for col, period in temporal_cyclic.items():\n",
        "    if col in df_features.columns:\n",
        "        df_features[f'{col}_sin'] = np.sin(2 * np.pi * df_features[col] / period)\n",
        "        df_features[f'{col}_cos'] = np.cos(2 * np.pi * df_features[col] / period)\n",
        "        df_features = df_features.drop(columns=[col])\n",
        "        print(f'   ✅ {col} → {col}_sin, {col}_cos')\n",
        "\n",
        "# ===== [4.4] FREQUENCY ENCODING PARA ALTA CARDINALIDADE =====\n",
        "print(f'\\n🏷️  Frequency Encoding para Alta Cardinalidade...')\n",
        "high_cardinality_cols = ['grupo_designado', 'subcategoria', 'produto']\n",
        "\n",
        "for col in high_cardinality_cols:\n",
        "    if col in df_features.columns:\n",
        "        freq_map = df_features[col].value_counts(normalize=True).to_dict()\n",
        "        df_features[col] = df_features[col].map(freq_map).fillna(0)\n",
        "        print(f'   ✅ {col} → Frequency-encoded ({len(freq_map)} unique values → 1 feature)')\n",
        "\n",
        "# ===== [4.5] ONE-HOT ENCODING PARA BAIXA CARDINALIDADE =====\n",
        "print(f'\\n📦 One-Hot Encoding para Baixa Cardinalidade...')\n",
        "low_cardinality_cols = ['categoria', 'turno_abertura']\n",
        "low_cardinality_cols = [c for c in low_cardinality_cols if c in df_features.columns]\n",
        "\n",
        "if low_cardinality_cols:\n",
        "    # Preencher NaN com 'unknown'\n",
        "    for col in low_cardinality_cols:\n",
        "        df_features[col] = df_features[col].fillna('unknown').astype(str)\n",
        "    \n",
        "    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore', max_categories=50)\n",
        "    X_ohe = encoder.fit_transform(df_features[low_cardinality_cols])\n",
        "    feature_names_ohe = encoder.get_feature_names_out(low_cardinality_cols)\n",
        "    X_ohe_df = pd.DataFrame(X_ohe, columns=feature_names_ohe, index=df_features.index)\n",
        "    \n",
        "    # Remover colunas originais e adicionar OHE\n",
        "    df_features = df_features.drop(columns=low_cardinality_cols)\n",
        "    df_features = pd.concat([df_features, X_ohe_df], axis=1)\n",
        "    \n",
        "    print(f'   ✅ {low_cardinality_cols} → {X_ohe.shape[1]} features OHE')\n",
        "\n",
        "# ===== [4.6] STANDARDSCALER =====\n",
        "print(f'\\n⚖️  StandardScaler Normalization...')\n",
        "scaler = StandardScaler()\n",
        "X_scaled = scaler.fit_transform(df_features.fillna(0))\n",
        "\n",
        "print(f'\\n✅ Features Finais:')\n",
        "print(f'   Antes (OHE explosion): 680 features')\n",
        "print(f'   Depois (CAUSA only + encoding otimizado): {X_scaled.shape[1]} features')\n",
        "print(f'   Redução: {(1 - X_scaled.shape[1]/680)*100:.1f}%')\n",
        "print(f'   Shape: {X_scaled.shape}')\n",
        "print(f'\\n✅ Preparação completa!')\n"
    ]
}

# ============================================================================
# CELL 4B (NOVA): Feature Selection Impact Visualization
# ============================================================================
cell_4b = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# ===== [4b] VISUALIZAÇÃO: IMPACTO DA SELEÇÃO DE FEATURES =====\n",
        "print('\\n📊 VISUALIZAÇÃO: Feature Selection Impact')\n",
        "\n",
        "fig, axes = plt.subplots(1, 3, figsize=(16, 5))\n",
        "fig.suptitle('Feature Selection Impact: CAUSA + Encoding Otimizado', fontsize=14, fontweight='bold')\n",
        "\n",
        "# [1] Barplot: Features Antes vs Depois\n",
        "features_comparison = ['Antes (OHE Explosion)', 'Depois (CAUSA only)']\n",
        "features_count = [680, X_scaled.shape[1]]\n",
        "colors_comp = ['#E53935', '#43A047']\n",
        "bars = axes[0].bar(features_comparison, features_count, color=colors_comp, edgecolor='black', linewidth=2)\n",
        "axes[0].set_ylabel('Número de Features', fontweight='bold')\n",
        "axes[0].set_title('1. Redução de Features')\n",
        "axes[0].grid(axis='y', alpha=0.3)\n",
        "for bar, count in zip(bars, features_count):\n",
        "    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,\n",
        "                f'{count}\\nfeatures', ha='center', va='bottom', fontweight='bold', fontsize=11)\n",
        "\n",
        "# [2] Pie Chart: Qual % foi removido e por quê\n",
        "removed_count = 680 - X_scaled.shape[1]\n",
        "kept_count = X_scaled.shape[1]\n",
        "sizes = [kept_count, removed_count]\n",
        "labels_pie = [f'Mantidas\\n({kept_count})\\nCAUSA only', f'Removidas\\n({removed_count})\\nEFEITO, OHE\\nexpl., NULL']\n",
        "colors_pie = ['#43A047', '#E53935']\n",
        "explode = (0.05, 0.1)\n",
        "axes[1].pie(sizes, labels=labels_pie, colors=colors_pie, autopct='%1.1f%%',\n",
        "           explode=explode, startangle=90, textprops={'fontsize': 11, 'weight': 'bold'})\n",
        "axes[1].set_title('2. Features Removidas vs Mantidas')\n",
        "\n",
        "# [3] Heatmap de Correlação Pós-Seleção (sample)\n",
        "# Reconstruir dataframe com feature nomes para análise\n",
        "if X_scaled.shape[1] <= 50:  # Se temos poucos features, mostrar todos\n",
        "    X_scaled_df = pd.DataFrame(X_scaled)\n",
        "    corr_post = X_scaled_df.corr()\n",
        "    # Mostrar apenas algumas features para legibilidade\n",
        "    sns.heatmap(corr_post.iloc[:15, :15], annot=False, cmap='coolwarm', center=0,\n",
        "               ax=axes[2], cbar_kws={'label': 'Correlação'}, vmin=-1, vmax=1)\n",
        "    axes[2].set_title('3. Correlação Pós-Seleção (primeiras 15 features)')\n",
        "else:\n",
        "    X_scaled_df = pd.DataFrame(X_scaled)\n",
        "    corr_post = X_scaled_df.corr()\n",
        "    sns.heatmap(corr_post.iloc[:20, :20], annot=False, cmap='coolwarm', center=0,\n",
        "               ax=axes[2], cbar_kws={'label': 'Correlação'}, vmin=-1, vmax=1)\n",
        "    axes[2].set_title('3. Correlação Pós-Seleção (primeiras 20 features)')\n",
        "\n",
        "plt.tight_layout()\n",
        "feat_selection_path = os.path.join(Path(r'D:\\Projetos\\AWS_Portifolio\\Projeto aws\\data\\ml\\kmeans'), 'feature_selection_impact.png')\n",
        "fig.savefig(feat_selection_path, dpi=100, bbox_inches='tight')\n",
        "plt.close()\n",
        "\n",
        "print(f'\\n✅ Feature Selection Impact salva em: {feat_selection_path}')\n"
    ]
}

# ============================================================================
# INSERIR CÉLULAS NOVAS
# ============================================================================

# Inserir célula 3b após célula 3
nb['cells'].insert(4, cell_3b)
print('[OK] Celula 3b (EDA) inserida apos celula 3')

# Reescrever célula 4 (agora na posição 5 após inserção de 3b)
nb['cells'][5] = cell_4_new
print('[OK] Celula 4 reescrita com CAUSA/EFEITO + encoding otimizado')

# Inserir célula 4b após célula 4 (posição 6)
nb['cells'].insert(6, cell_4b)
print('[OK] Celula 4b (Feature Selection Impact) inserida apos celula 4')

# ============================================================================
# SALVAR NOTEBOOK MODIFICADO
# ============================================================================
with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print(f'\n[OK] Notebook salvo com sucesso!')
print(f'   Caminho: {nb_path}')
print(f'   Total de celulas agora: {len(nb["cells"])}')
print(f'\n[INFO] Proximas etapas:')
print(f'   1. Executar as novas celulas para validar feature selection')
print(f'   2. Verificar que X_scaled.shape[1] < 100 (esperado ~30-40 features)')
print(f'   3. Rodar PCA e K-Means com novo feature set')
print(f'   4. Esperar clusters balanceados (todos >15%)')
