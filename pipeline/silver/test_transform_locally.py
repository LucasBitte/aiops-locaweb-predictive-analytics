"""
Teste local do pipeline Silver (sem S3)
Para validar a logica antes de rodar no Glue
"""

import pandas as pd
from datetime import datetime

print("\n" + "="*70)
print("  TEST: Bronze to Silver Transformation (Local)")
print("="*70 + "\n")

# Simular dados do Bronze
print("[INFO] Criando dados simulados...")
data = {
    'Numero': ['INC001', 'INC002', 'INC003'],
    'Prioridade': ['1 - Critica', '2 - Alta', '3 - Media'],
    'Produto': ['Hospedagem', 'Email', 'Hospedagem'],
    'Categoria': ['Infraestrutura', 'Email', 'Infraestrutura'],
    'Subcategoria': ['Servidor', 'Caixa Postal', 'Rede'],
    'Grupo_designado': ['Ops', 'Email', 'Ops'],
    'Aberto': ['2025-01-10', '2025-01-15', '2025-02-01'],
    'Resolvido': ['2025-01-11', '2025-01-16', '2025-02-02'],
    'Encerrado': ['2025-01-12', '2025-01-17', '2025-02-03'],
    'Duracao': [120, 240, 1440],  # minutos
    'Status': ['Fechado', 'Fechado', 'Fechado'],
    'Entrou_para_KPI': [True, True, False],
    'KPI_Violado': [False, True, False],
    'Incidente_Pai': [None, None, 'INC001'],
    'Codigo_de_fechamento': ['RESOLVIDO', 'RESOLVIDO', 'DUPLICADO'],
    'Solucao': ['Reiniciou servidor', 'Resetou senha', 'Ticket duplicado'],
    'Aberto_por': ['usuario1', 'usuario2', 'usuario3'],
    'Descricao_resumida': ['Servidor Down', 'Email nao acessa', 'Problema de rede']
}

df = pd.DataFrame(data)
print(f"[INFO] Dataset criado: {len(df)} registros, {len(df.columns)} colunas\n")

# 1. Validar schema
print("[INFO] Validando schema...")
expected_cols = [
    'Numero', 'Prioridade', 'Produto', 'Categoria', 'Subcategoria',
    'Grupo_designado', 'Aberto', 'Resolvido', 'Encerrado', 'Duracao',
    'Status', 'Entrou_para_KPI', 'KPI_Violado', 'Incidente_Pai',
    'Codigo_de_fechamento', 'Solucao', 'Aberto_por', 'Descricao_resumida'
]
print(f"  Colunas esperadas: {len(expected_cols)}")
print(f"  Colunas presentes: {len(df.columns)}")

# 2. Tratar nulos
print("[INFO] Tratando nulos...")
fillna_values = {
    "Aberto": "1900-01-01",
    "Resolvido": "1900-01-01",
    "Encerrado": "1900-01-01",
    "Duracao": 0,
    "Codigo_de_fechamento": "DESCONHECIDO",
    "Solucao": "NAO REGISTRADA",
    "Descricao_resumida": "SEM DESCRICAO"
}
df = df.fillna(fillna_values)

# 3. Criar features
print("[INFO] Criando features...")
df['Data_Abertura'] = pd.to_datetime(df['Aberto'])
df['Ano_Mes'] = df['Data_Abertura'].dt.strftime('%Y-%m')

df['Prioridade_Num'] = df['Prioridade'].map({
    '1 - Critica': 1,
    '2 - Alta': 2,
    '3 - Media': 3,
    '4 - Baixa': 4
}).fillna(5)

df['Exige_Intervencao'] = ((df['Entrou_para_KPI'] == True) & (df['KPI_Violado'] == True)).astype(int)
df['Possui_Pai'] = (df['Incidente_Pai'].notna()).astype(int)
df['Duracao_Horas'] = df['Duracao'] / 60.0

print(f"  Features criadas: {['Data_Abertura', 'Ano_Mes', 'Prioridade_Num', 'Exige_Intervencao', 'Possui_Pai', 'Duracao_Horas']}")

# 4. Calcular target
print("[INFO] Calculando Target_Risco_SLA...")
df['Target_Risco_SLA'] = (
    (df['KPI_Violado'] == True) |
    (df['Prioridade_Num'] <= 2) |
    (df['Duracao_Horas'] > 8)
).astype(int)

# 5. Filtrar por data
print("[INFO] Filtrando registros a partir de 2025-01-01...")
MIN_DATE = pd.to_datetime("2025-01-01")
df = df[df['Data_Abertura'] >= MIN_DATE]

print(f"[INFO] Registros finais: {len(df)}")

# 6. Agrupar por Ano_Mes
print("[INFO] Agrupando por Ano_Mes...")
for mes, grupo in df.groupby('Ano_Mes'):
    print(f"  {mes}: {len(grupo)} registros")

print("\n" + "="*70)
print("[SUCCESS] TRANSFORMACAO CONCLUIDA")
print("="*70)
print(f"\nEstatisticas:")
print(f"  Total de registros: {len(df)}")
print(f"  Colunas finais: {len(df.columns)}")
print(f"  Particoes: {df['Ano_Mes'].nunique()}")

print(f"\nTarget_Risco_SLA:")
print(f"  Risco: {(df['Target_Risco_SLA'] == 1).sum()} registros")
print(f"  Normal: {(df['Target_Risco_SLA'] == 0).sum()} registros")

print(f"\nDados de amostra:")
print(df[['Numero', 'Prioridade', 'Duracao_Horas', 'Target_Risco_SLA', 'Ano_Mes']].to_string())
