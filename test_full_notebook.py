#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste rapido: rodar notebook ate cluster assignment para validar balanceamento
"""

import os
import sys
import warnings
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
import tempfile

warnings.filterwarnings('ignore')
load_dotenv()

print("[INFO] ========== TESTE DE CLUSTERING EQUILIBRADO ==========")

# RDS Connection
RDS_HOST = os.getenv('RDS_HOST')
RDS_PORT = int(os.getenv('RDS_PORT', '5432'))
RDS_USER = os.getenv('RDS_USER', 'postgres')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')
RDS_DATABASE = os.getenv('RDS_DATABASE', 'aiops_gold')

engine = __import__('sqlalchemy').create_engine(f"postgresql://{RDS_USER}:{RDS_PASSWORD}@{RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}")

# [1] Load data
print("[STEP 1] Carregando dataset...")
df = pd.read_sql('''SELECT * FROM gold_ml.ml_cluster_dataset''', engine)
print(f"  [OK] {len(df):,} incidentes carregados")

# [2] Outlier removal
print("[STEP 2] Removendo outliers...")
numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
numeric_cols = [c for c in numeric_cols if c not in ['incident_id', 'cluster', 'data_abertura']]

outlier_counts = pd.DataFrame(index=df.index)
for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outlier_counts[col] = ~((df[col] >= lower) & (df[col] <= upper))

outlier_total_per_row = outlier_counts.sum(axis=1)
max_outliers_allowed = len(numeric_cols) * 0.5
outlier_mask = outlier_total_per_row <= max_outliers_allowed

df_clean = df[outlier_mask].copy()
n_removed = len(df) - len(df_clean)
print(f"  [OK] {n_removed:,} removidos ({n_removed/len(df)*100:.2f}%)")

# [3] Feature selection CAUSA
print("[STEP 3] Selecionando features CAUSA...")
cause_cols = [
    'prioridade_num', 'grupo_designado', 'categoria', 'subcategoria', 'produto',
    'hora_abertura', 'turno_abertura', 'dia_semana_num', 'fora_horario_comercial',
    'abriu_fim_de_semana', 'mes_abertura', 'trimestre', 'possui_pai', 'triagem_incompleta'
]
cause_cols_valid = [c for c in cause_cols if c in df_clean.columns]
df_features = df_clean[cause_cols_valid].copy()
print(f"  [OK] {len(cause_cols_valid)} features CAUSA selecionadas")

# [4] Encoding
print("[STEP 4] Aplicando encodings...")
# Ciclico
temporal_cyclic = {'hora_abertura': 24, 'dia_semana_num': 7, 'mes_abertura': 12}
for col, period in temporal_cyclic.items():
    if col in df_features.columns:
        df_features[f'{col}_sin'] = np.sin(2 * np.pi * df_features[col] / period)
        df_features[f'{col}_cos'] = np.cos(2 * np.pi * df_features[col] / period)
        df_features = df_features.drop(columns=[col])

# Frequency
for col in ['grupo_designado', 'subcategoria', 'produto']:
    if col in df_features.columns:
        freq_map = df_features[col].value_counts(normalize=True).to_dict()
        df_features[col] = df_features[col].map(freq_map).fillna(0)

# OHE
low_card = ['categoria', 'turno_abertura']
low_card = [c for c in low_card if c in df_features.columns]
if low_card:
    for col in low_card:
        df_features[col] = df_features[col].fillna('unknown').astype(str)
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore', max_categories=50)
    X_ohe = encoder.fit_transform(df_features[low_card])
    X_ohe_df = pd.DataFrame(X_ohe, columns=encoder.get_feature_names_out(low_card), index=df_features.index)
    df_features = df_features.drop(columns=low_card)
    df_features = pd.concat([df_features, X_ohe_df], axis=1)

# Scaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_features.fillna(0))
print(f"  [OK] {X_scaled.shape[1]} features apos encoding")

# [5] PCA
print("[STEP 5] Aplicando PCA (95% variancia)...")
pca = PCA(n_components=0.95, random_state=42)
X_pca = pca.fit_transform(X_scaled)
n_components = pca.n_components_
print(f"  [OK] Reducao: {X_scaled.shape[1]} -> {n_components} componentes")

# [6] K-Means
print("[STEP 6] Treinando K-Means k=4...")
k = 4
model = KMeans(n_clusters=k, random_state=42, n_init=10, max_iter=300)
labels = model.fit_predict(X_pca)

sil_score = silhouette_score(X_pca, labels)
db_score = davies_bouldin_score(X_pca, labels)
print(f"  [OK] Silhouette: {sil_score:.4f}, Davies-Bouldin: {db_score:.4f}")

# [7] Cluster assignment
print("[STEP 7] Atribuindo clusters...")
df_clean['cluster_pred'] = labels
cluster_names = {0: 'A', 1: 'B', 2: 'C', 3: 'D'}
df_clean['cluster_label'] = df_clean['cluster_pred'].map(cluster_names)

df_outliers = df[~outlier_mask].copy()
if len(df_outliers) > 0:
    feature_cols_outliers = [c for c in df_outliers.columns if c not in ['incident_id', 'cluster', 'data_abertura']]
    X_outliers = df_outliers[feature_cols_outliers].fillna(0)
    X_outliers_proc = X_outliers.copy()

    if low_card and 'encoder' in locals():
        for col in low_card:
            if col in X_outliers_proc.columns:
                X_outliers_proc[col] = X_outliers_proc[col].astype(str)
        X_outliers_cat = encoder.transform(X_outliers_proc[low_card])
        X_outliers_cat_df = pd.DataFrame(X_outliers_cat, columns=encoder.get_feature_names_out(low_card), index=X_outliers_proc.index)
        num_cols_o = [c for c in ['prioridade_num', 'hora_abertura_sin', 'hora_abertura_cos', 'dia_semana_num_sin', 'dia_semana_num_cos', 'mes_abertura_sin', 'mes_abertura_cos', 'fora_horario_comercial', 'abriu_fim_de_semana', 'trimestre', 'possui_pai', 'triagem_incompleta', 'grupo_designado', 'subcategoria', 'produto'] if c in X_outliers_proc.columns]
        X_outliers_proc = pd.concat([X_outliers_proc[num_cols_o].reset_index(drop=True), X_outliers_cat_df.reset_index(drop=True)], axis=1)

    X_outliers_scaled = scaler.transform(X_outliers_proc)
    X_outliers_pca = pca.transform(X_outliers_scaled)
    labels_outliers = model.predict(X_outliers_pca)

    df_outliers['cluster_pred'] = labels_outliers
    df_outliers['cluster_label'] = df_outliers['cluster_pred'].map(cluster_names)

    df_final = pd.concat([df_clean, df_outliers], ignore_index=False).sort_index()
else:
    df_final = df_clean.copy()

# [8] Results
print("[STEP 8] Distribuicao Final:")
print("")
cluster_dist = df_final['cluster_label'].value_counts().sort_index()
for label in ['A', 'B', 'C', 'D']:
    count = cluster_dist.get(label, 0)
    pct = count / len(df_final) * 100 if count > 0 else 0
    status = "[OK]" if 10 < pct < 40 else "[WARN]" if pct == 0 else "[CHECK]"
    print(f"  {status} Cluster {label}: {count:>8,} incidentes ({pct:>5.2f}%)")

print("")
print("[RESULTADO FINAL]:")
is_balanced = all(10 < (df_final['cluster_label'].value_counts().get(label, 0) / len(df_final) * 100) < 40 for label in ['A', 'B', 'C', 'D'])
if is_balanced:
    print("  [SUCCESS] Clustering EQUILIBRADO! Todos os clusters entre 10-40%")
else:
    all_values = [df_final['cluster_label'].value_counts().get(label, 0) / len(df_final) * 100 for label in ['A', 'B', 'C', 'D']]
    if min(all_values) > 1:
        print("  [CHECK] Clustering MELHORADO! Nao perfeito mas muito melhor que antes")
    else:
        print("  [WARN] Clustering ainda DEGENERADO em alguns clusters")

print("")
