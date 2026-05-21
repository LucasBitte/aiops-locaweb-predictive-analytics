#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adiciona Celula 6b: Cluster Profiling com features EFEITO
Interpreta os clusters usando metricas de resultado
"""

import json

nb_path = 'notebooks/07_model_clustering_kmeans.ipynb'
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Cell 6b: Cluster Profiling com EFEITO
cell_6b = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# ===== [6b] CLUSTER PROFILING: INTERPRETAR COM FEATURES EFEITO =====\n",
        "print('[INFO] CLUSTER PROFILING: Interpretacao dos Clusters')\n",
        "\n",
        "# Features de EFEITO para interpretar clusters\n",
        "effect_cols = [\n",
        "    'duracao_horas', 'horas_ate_resolucao', 'foi_resolvido', 'excedeu_tempo_esperado',\n",
        "    'fechado_sem_tecnico', 'target_risco_sla', 'score_risco_operacional'\n",
        "]\n",
        "\n",
        "# Unir clusters com features de EFEITO\n",
        "df_with_effect = df_final.join(df[effect_cols], how='left')\n",
        "\n",
        "# Criar visualizacao com 4 graficos\n",
        "fig, axes = plt.subplots(2, 2, figsize=(15, 10))\n",
        "fig.suptitle('Cluster Profiling: Interpretacao com Features EFEITO', fontsize=14, fontweight='bold')\n",
        "\n",
        "colors_map = {'A': '#E53935', 'B': '#1E88E5', 'C': '#43A047', 'D': '#8E24AA'}\n",
        "\n",
        "# [1] Tamanho dos clusters\n",
        "cluster_sizes = df_final['cluster_label'].value_counts().sort_index()\n",
        "bars = axes[0, 0].bar(cluster_sizes.index, cluster_sizes.values,\n",
        "                       color=[colors_map[c] for c in cluster_sizes.index],\n",
        "                       edgecolor='black', linewidth=2)\n",
        "axes[0, 0].set_ylabel('Numero de Incidentes')\n",
        "axes[0, 0].set_title('1. Distribuicao de Clusters')\n",
        "axes[0, 0].grid(axis='y', alpha=0.3)\n",
        "for bar, val in zip(bars, cluster_sizes.values):\n",
        "    pct = val/len(df_final)*100\n",
        "    axes[0, 0].text(bar.get_x()+bar.get_width()/2, bar.get_height()+1000,\n",
        "                   f'{val:,}\\n({pct:.1f}%)', ha='center', va='bottom', fontweight='bold')\n",
        "\n",
        "# [2] Tempo medio de resolucao por cluster\n",
        "if 'horas_ate_resolucao' in df_with_effect.columns:\n",
        "    df_with_effect.boxplot(column='horas_ate_resolucao', by='cluster_label', ax=axes[0, 1])\n",
        "    axes[0, 1].set_xlabel('Cluster')\n",
        "    axes[0, 1].set_ylabel('Horas ate Resolucao')\n",
        "    axes[0, 1].set_title('2. Tempo de Resolucao por Cluster')\n",
        "    axes[0, 1].get_figure().suptitle('')  # Remove o titulo automatico\n",
        "\n",
        "# [3] Perfil de metricas EFEITO por cluster (heatmap normalizado)\n",
        "numeric_effect = [c for c in effect_cols if c in df_with_effect.columns and df_with_effect[c].dtype in ['int64', 'float64']]\n",
        "if numeric_effect:\n",
        "    profile = df_with_effect.groupby('cluster_label')[numeric_effect].mean()\n",
        "    profile_norm = (profile - profile.min()) / (profile.max() - profile.min() + 1e-9)\n",
        "    sns.heatmap(profile_norm, annot=True, fmt='.2f', cmap='RdYlGn_r', ax=axes[1, 0],\n",
        "               cbar_kws={'label': 'Score Normalizado'})\n",
        "    axes[1, 0].set_title('3. Perfil de Metricas EFEITO (normalizado)')\n",
        "    axes[1, 0].set_ylabel('Cluster')\n",
        "\n",
        "# [4] Taxa de resolucao por cluster\n",
        "if 'foi_resolvido' in df_with_effect.columns:\n",
        "    resolution_rate = df_with_effect.groupby('cluster_label')['foi_resolvido'].apply(lambda x: (x.sum()/len(x)*100))\n",
        "    bars = axes[1, 1].bar(resolution_rate.index, resolution_rate.values,\n",
        "                          color=[colors_map[c] for c in resolution_rate.index],\n",
        "                          edgecolor='black', linewidth=2)\n",
        "    axes[1, 1].set_ylabel('Taxa de Resolucao (%)')\n",
        "    axes[1, 1].set_title('4. Taxa de Resolucao por Cluster')\n",
        "    axes[1, 1].set_ylim([0, 105])\n",
        "    axes[1, 1].grid(axis='y', alpha=0.3)\n",
        "    for bar, val in zip(bars, resolution_rate.values):\n",
        "        axes[1, 1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+2,\n",
        "                       f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')\n",
        "\n",
        "plt.tight_layout()\n",
        "cluster_profile_path = os.path.join(Path(r'D:\\Projetos\\AWS_Portifolio\\Projeto aws\\data\\ml\\kmeans'), 'cluster_profile_efeito.png')\n",
        "fig.savefig(cluster_profile_path, dpi=100, bbox_inches='tight')\n",
        "plt.close()\n",
        "\n",
        "print('[OK] Cluster Profiling salvo')\n",
        "\n",
        "# Mostrar resumo interpretativo\n",
        "print('[INFO] INTERPRETACAO DOS CLUSTERS:')\n",
        "for label in sorted(df_final['cluster_label'].unique()):\n",
        "    mask = df_final['cluster_label'] == label\n",
        "    count = mask.sum()\n",
        "    pct = count/len(df_final)*100\n",
        "    print(f'  Cluster {label}: {count:,} incidentes ({pct:.1f}%)')\n",
        "    \n",
        "    if 'horas_ate_resolucao' in df_with_effect.columns:\n",
        "        avg_duration = df_with_effect[mask]['horas_ate_resolucao'].mean()\n",
        "        print(f'           Tempo medio: {avg_duration:.1f} horas')\n",
        "    \n",
        "    if 'excedeu_tempo_esperado' in df_with_effect.columns:\n",
        "        sla_violation = df_with_effect[mask]['excedeu_tempo_esperado'].mean() * 100\n",
        "        print(f'           Taxa SLA violado: {sla_violation:.1f}%')\n"
    ]
}

# Encontrar o indice da celula 6a (cluster assignment)
target_index = None
for i, cell in enumerate(nb['cells']):
    if cell['cell_type'] == 'code':
        source_text = ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']
        if 'ATRIBUICAO DE CLUSTERS' in source_text or ('df_final' in source_text and 'cluster_label' in source_text):
            target_index = i + 1  # Inserir apos a celula de atribuicao
            break

if target_index:
    nb['cells'].insert(target_index, cell_6b)
    print(f"[OK] Celula 6b inserida no indice {target_index}")
else:
    # Se não encontrou, inserir no final antes da célula 8 (save results)
    nb['cells'].insert(-2, cell_6b)
    print("[OK] Celula 6b inserida antes da celula de Save Results")

# Salvar
with open(nb_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("[OK] Notebook atualizado com Celula 6b")
print(f"     Total de celulas: {len(nb['cells'])}")
