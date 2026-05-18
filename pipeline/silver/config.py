"""
Configurações globais para transformação Bronze → Silver
"""

# === CAMINHOS S3 ===
BRONZE_PATH = "s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet"
SILVER_PATH = "s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet"
SILVER_BACKUP_PATH = "s3://aiops-locaweb-datalake-2026/silver_backup/"

# === FILTROS TEMPORAIS ===
MIN_DATE = "2025-01-01"
PARTITION_COLS = ["Ano_Mes"]

# === SCHEMA ESPERADO (BRONZE) ===
EXPECTED_SCHEMA_COLS = [
    'Número', 'Prioridade', 'Produto', 'Categoria', 'Subcategoria',
    'Grupo_designado', 'Aberto', 'Resolvido', 'Encerrado', 'Duração',
    'Status', 'Entrou_para_KPI', 'KPI_Violado', 'Incidente_Pai',
    'Código_de_fechamento', 'Solução', 'Aberto_por', 'Descrição_resumida'
]

# === FEATURES ENGINEERED ===
FEATURE_COLS = [
    'Exige_Intervencao',
    'Prioridade_Num',
    'Possui_Pai',
    'Duracao_Horas',
    'Data_Abertura',
    'Ano_Mes',
    'KPI_Status_Int',
    'Target_Risco_SLA'
]

# === REGRAS DE FILLNA (NULOS) ===
FILLNA_RULES = {
    'Produto': 'Não Classificado',
    'Categoria': 'Não Classificado',
    'Subcategoria': 'Não Informada',
    'Incidente_Pai': 'Independente',
    'Código_de_fechamento': 'Não Encerrado',
    'Solução': 'Sem Descrição'
}

# === CONFIGURAÇÃO GLUE (Otimizado para AWS Free Tier) ===
# Free Tier: 100 DPU-horas/mês = 6.000 DPU-minutos/mês
# G.1X: 1 DPU/worker × 3 workers × 60 min = 180 DPU-min por execução
# 180 × 30 dias = 5.400 DPU-min/mês ✅ (com margem de 600 DPU-min)
GLUE_JOB_NAME = "transform_bronze_to_silver"
GLUE_VERSION = "4.0"
GLUE_WORKER_TYPE = "G.1X"        # 1 DPU/worker (era G.2X = 2 DPUs)
GLUE_NUM_WORKERS = 3              # 3 workers (era 10)
GLUE_TIMEOUT = 60                 # minutos (suficiente para 41.4k registros)
# Tempo esperado: 15-25 minutos (vs 10-15 anteriormente)
# Performance: ~2x mais lento, mas 90% mais barato ($0 vs $150-200/mês)

# === LIMITES DE VALIDAÇÃO ===
MIN_RECORDS_SILVER = 35000  # Alerta se < que isso
MAX_NULL_RATIO = 0.05  # Alerta se > 5%
MAX_VIOLATION_RATE = 0.02  # Alerta se > 2%

# === CONFIGURAÇÃO DE LOG ===
LOG_LEVEL = "INFO"
LOG_FORMAT = "[%(asctime)s] %(levelname)s: %(message)s"
