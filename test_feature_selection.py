#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste rápido do feature selection: verificar se CAUSA + encoding funciona
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sqlalchemy import create_engine

load_dotenv()

# Conectar ao RDS
RDS_HOST = os.getenv('RDS_HOST')
RDS_PORT = int(os.getenv('RDS_PORT', '5432'))
RDS_USER = os.getenv('RDS_USER', 'postgres')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')
RDS_DATABASE = os.getenv('RDS_DATABASE', 'aiops_gold')

engine = create_engine(f"postgresql://{RDS_USER}:{RDS_PASSWORD}@{RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}")

print("[INFO] Carregando dados do RDS...")
df = pd.read_sql('''SELECT * FROM gold_ml.ml_cluster_dataset''', engine)
print(f"[OK] Dataset carregado: {len(df):,} incidentes, {len(df.columns)} colunas")

# Feature selection CAUSA
cause_cols = [
    'prioridade_num', 'grupo_designado', 'categoria', 'subcategoria', 'produto',
    'hora_abertura', 'turno_abertura', 'dia_semana_num', 'fora_horario_comercial',
    'abriu_fim_de_semana', 'mes_abertura', 'trimestre', 'possui_pai', 'triagem_incompleta'
]

cause_cols_valid = [c for c in cause_cols if c in df.columns]
print(f"[OK] CAUSA features: {len(cause_cols_valid)}")

df_features = df[cause_cols_valid].copy()

# Outlier removal
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
df_features = df_features[outlier_mask].copy()
print(f"[OK] Outlier removal: {len(df) - len(df_clean):,} removidos, {len(df_clean):,} mantidos")

# Encoding ciclico
print("[INFO] Aplicando encoding ciclico para features temporais...")
temporal_cyclic = {
    'hora_abertura': 24,
    'dia_semana_num': 7,
    'mes_abertura': 12
}

for col, period in temporal_cyclic.items():
    if col in df_features.columns:
        df_features[f'{col}_sin'] = np.sin(2 * np.pi * df_features[col] / period)
        df_features[f'{col}_cos'] = np.cos(2 * np.pi * df_features[col] / period)
        df_features = df_features.drop(columns=[col])

# Frequency encoding
print("[INFO] Aplicando frequency encoding para alta cardinalidade...")
high_cardinality_cols = ['grupo_designado', 'subcategoria', 'produto']

for col in high_cardinality_cols:
    if col in df_features.columns:
        freq_map = df_features[col].value_counts(normalize=True).to_dict()
        df_features[col] = df_features[col].map(freq_map).fillna(0)

# One-Hot encoding
print("[INFO] Aplicando OHE para baixa cardinalidade...")
low_cardinality_cols = ['categoria', 'turno_abertura']
low_cardinality_cols = [c for c in low_cardinality_cols if c in df_features.columns]

if low_cardinality_cols:
    for col in low_cardinality_cols:
        df_features[col] = df_features[col].fillna('unknown').astype(str)

    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore', max_categories=50)
    X_ohe = encoder.fit_transform(df_features[low_cardinality_cols])
    feature_names_ohe = encoder.get_feature_names_out(low_cardinality_cols)
    X_ohe_df = pd.DataFrame(X_ohe, columns=feature_names_ohe, index=df_features.index)

    df_features = df_features.drop(columns=low_cardinality_cols)
    df_features = pd.concat([df_features, X_ohe_df], axis=1)

# StandardScaler
print("[INFO] Aplicando StandardScaler...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_features.fillna(0))

print("")
print("[OK] RESULTADO DO FEATURE SELECTION:")
print(f"     Features ANTES (OHE explosion): 680")
print(f"     Features DEPOIS (CAUSA only): {X_scaled.shape[1]}")
print(f"     Reducao: {(1 - X_scaled.shape[1]/680)*100:.1f}%")
print(f"     Shape final: {X_scaled.shape}")
print("")

if X_scaled.shape[1] < 100:
    print("[SUCCESS] Feature selection FUNCIONOU! Less than 100 features")
else:
    print("[WARN] Feature selection ainda resultou em muitos features:", X_scaled.shape[1])
