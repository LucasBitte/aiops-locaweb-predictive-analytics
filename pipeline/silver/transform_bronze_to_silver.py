"""
Job Apache Glue: Transformacao Bronze to Silver
Converte dados brutos do ITSM em dataset refinado para modelagem ML.

Entrada:  s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet
Saida:    s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet

Epico: E5 - Analytics Exploratoria
Versao: 1.0
Data: 2026-05-18
"""

import sys
import os
import traceback
from datetime import datetime
from io import BytesIO

# Detectar ambiente (Glue vs local)
IS_GLUE_ENV = 'SPARK_HOME' in os.environ or 'GLUE_VERSION' in os.environ

if IS_GLUE_ENV:
    # Imports do Glue (rodando no AWS Glue)
    from awsglue.transforms import *
    from awsglue.utils import getResolvedOptions
    from pyspark.context import SparkContext
    from awsglue.context import GlueContext
    from awsglue.job import Job
    from pyspark.sql import functions as F
    from pyspark.sql.types import *
else:
    # Imports locais (desenvolvimento)
    try:
        from pyspark.sql import functions as F, SparkSession
        from pyspark.sql.types import *
    except ImportError:
        print("[ERROR] PySpark nao instalado. Para testar localmente:")
        print("  pip install pyspark")
        sys.exit(1)

try:
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError
except ImportError:
    boto3 = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# === CONFIG ===
BRONZE_PATH = "s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet"
SILVER_PATH = "s3://aiops-locaweb-datalake-2026/silver"
MIN_DATE = "2025-01-01"
PARTITION_COLS = ["Ano_Mes"]

EXPECTED_SCHEMA_COLS = [
    'Numero', 'Prioridade', 'Produto', 'Categoria', 'Subcategoria',
    'Grupo_designado', 'Aberto', 'Resolvido', 'Encerrado', 'Duracao',
    'Status', 'Entrou_para_KPI', 'KPI_Violado', 'Incidente_Pai',
    'Codigo_de_fechamento', 'Solucao', 'Aberto_por', 'Descricao_resumida'
]


# === LOGGER ===
class Logger:
    def __init__(self, job_name):
        self.job_name = job_name

    def info(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] [INFO] {msg}")

    def error(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] [ERROR] {msg}")

    def section(self, title):
        print("\n" + "="*70)
        print(f"  {title}")
        print("="*70 + "\n")

    def dataframe_info(self, df):
        try:
            count = df.count()
            self.info(f"Registros: {count}, Colunas: {len(df.columns)}")
        except:
            self.info(f"Colunas: {len(df.columns)}")


# === VALIDATORS ===
def validate_schema(df):
    cols_existentes = set(df.columns)
    log.info(f"Colunas encontradas: {list(df.columns)}")

    return df


def validate_not_empty(df):
    count = df.count()
    if count == 0:
        raise Exception("DataFrame vazio!")
    return count


# === TRANSFORMATIONS ===
def create_all_features(df):
    log.info("Criando features de engenharia...")

    df = df.withColumn("Data_Abertura", F.to_date(F.col("Aberto")))
    df = df.withColumn("Ano_Mes", F.date_format(F.col("Data_Abertura"), "yyyy-MM"))

    df = df.withColumn("Prioridade_Num",
        F.when(F.col("Prioridade") == "1 - Critica", 1)
         .when(F.col("Prioridade") == "2 - Alta", 2)
         .when(F.col("Prioridade") == "3 - Media", 3)
         .when(F.col("Prioridade") == "4 - Baixa", 4)
         .otherwise(5)
    )

    df = df.withColumn("Exige_Intervencao",
        F.when((F.col("Entrou_para_KPI") == True) | (F.col("Entrou_para_KPI") == "Sim"), 1)
         .otherwise(0)
    )

    df = df.withColumn("Possui_Pai",
        F.when(F.col("Incidente_Pai").isNotNull(), 1).otherwise(0)
    )

    df = df.withColumn("Duracao_Horas",
        F.when(F.col("Duracao").isNotNull(), F.col("Duracao").cast("double") / 60.0)
         .otherwise(0)
    )

    log.info(f"Features criadas: Data_Abertura, Ano_Mes, Prioridade_Num, Exige_Intervencao, Possui_Pai, Duracao_Horas")
    return df


def calculate_target_risco_sla(df):
    log.info("Calculando Target_Risco_SLA...")

    df = df.withColumn("Target_Risco_SLA",
        F.when(F.col("KPI_Violado") == True, 1)
         .when(F.col("KPI_Violado") == "Sim", 1)
         .when(F.col("Prioridade_Num") <= 2, 1)
         .when(F.col("Duracao_Horas") > 8, 1)
         .otherwise(0)
    )

    return df


def handle_nulls(df):
    log.info("Tratando valores nulos...")

    fillna_values = {
        "Aberto": "1900-01-01",
        "Resolvido": "1900-01-01",
        "Encerrado": "1900-01-01",
        "Duracao": 0,
        "Codigo_de_fechamento": "DESCONHECIDO",
        "Solucao": "NAO REGISTRADA",
        "Descricao_resumida": "SEM DESCRICAO"
    }

    for col, val in fillna_values.items():
        if col in df.columns:
            df = df.fillna({col: val})

    return df


# === SETUP ===
log = Logger("AIOps-Silver")

if IS_GLUE_ENV:
    args = getResolvedOptions(sys.argv, ['JOB_NAME'])
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
else:
    spark = SparkSession.builder \
        .appName("AIOps-Silver-Local") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    job = None


# === MAIN PIPELINE ===
try:
    log.section("INICIANDO JOB: BRONZE to SILVER")

    # 1. Ler dados Bronze
    log.info(f"Lendo dados do Bronze: {BRONZE_PATH}")
    df = spark.read.parquet(BRONZE_PATH)

    log.dataframe_info(df)

    # 2. Validar schema
    log.info("Validando schema...")
    df = validate_schema(df)

    # 3. Tratar nulos
    df = handle_nulls(df)

    # 4. Criar features
    df = create_all_features(df)

    # 5. Calcular target
    df = calculate_target_risco_sla(df)

    # 6. Filtrar por data minima
    log.info(f"Filtrando registros a partir de {MIN_DATE}")
    df = df.filter(F.col("Data_Abertura") >= F.lit(MIN_DATE))

    registros_finais = validate_not_empty(df)
    log.info(f"Registros para Silver: {registros_finais}")

    # 7. Salvar em Silver (particionado por Ano_Mes)
    log.info(f"Salvando em Silver: {SILVER_PATH}")
    silver_output = f"{SILVER_PATH}/incidents_silver_2025.parquet"

    df.repartition(4).write \
        .partitionBy(PARTITION_COLS) \
        .mode("overwrite") \
        .parquet(silver_output)

    log.info(f"[SUCCESS] Dados salvos em {silver_output}")

    # 8. Relatorio final
    log.section("RESUMO DA EXECUCAO")
    log.info(f"Total de registros processados: {registros_finais}")
    log.info(f"Colunas finais: {len(df.columns)}")
    log.info(f"Particoes criadas: {PARTITION_COLS}")
    log.info(f"Output: {silver_output}")

    if IS_GLUE_ENV:
        job.commit()

    log.info("[COMPLETED] Job concluido com sucesso!")

except Exception as e:
    log.error(f"Erro na pipeline: {str(e)}")
    log.error(traceback.format_exc())

    if IS_GLUE_ENV:
        job.commit()

    raise
