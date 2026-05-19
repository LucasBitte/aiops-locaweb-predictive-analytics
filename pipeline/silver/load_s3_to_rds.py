"""
Script: Importar Silver (S3 Parquet) → RDS PostgreSQL

Responsabilidade: Conectar Glue (S3) ao dbt (RDS)
- Lê Parquet gerado pelo Glue
- Importa para tabela raw_incidents_silver no RDS
- Cria índices para performance
- Log de sucesso/erro

Fluxo:
  Glue job (E5)
      ↓ (Parquet em S3)
  Este script
      ↓
  RDS raw_incidents_silver (pronto para dbt)

Épico: E5 (ponte Silver S3 → RDS)
Versão: 1.0
Data: 2026-05-18
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional
import traceback

# Data processing
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Database
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Numeric, DateTime
from sqlalchemy.types import VARCHAR, INT, DECIMAL, TIMESTAMP

# AWS
import boto3

# ============================================================================
# CONFIGURATION
# ============================================================================

# S3 paths (from Glue output)
S3_SILVER_PATH = os.getenv(
    'S3_SILVER_PATH',
    's3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet/'
)

# RDS connection
RDS_HOST = os.getenv('RDS_HOST', 'aiops-db.c9akciq32.us-east-1.rds.amazonaws.com')
RDS_PORT = int(os.getenv('RDS_PORT', 5432))
RDS_USER = os.getenv('RDS_USER', 'admin')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')
RDS_DATABASE = os.getenv('RDS_DATABASE', 'aiops')
RDS_SCHEMA = os.getenv('RDS_SCHEMA', 'dbt_dev')

# Table config
RDS_TABLE_NAME = 'raw_incidents_silver'
BATCH_SIZE = 10000

# ============================================================================
# LOGGING SETUP
# ============================================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# ============================================================================
# SPARK SESSION
# ============================================================================

spark = SparkSession \
    .builder \
    .appName("LoadSilverS3toRDS") \
    .config("spark.hadoop.fs.s3a.access.key", os.getenv('AWS_ACCESS_KEY_ID', '')) \
    .config("spark.hadoop.fs.s3a.secret.key", os.getenv('AWS_SECRET_ACCESS_KEY', '')) \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

# ============================================================================
# FUNCTIONS
# ============================================================================

def read_silver_from_s3() -> Optional:
    """Lê Parquet do S3 usando Spark."""
    logger.info(f"Lendo Silver de {S3_SILVER_PATH}...")

    try:
        df = spark.read.parquet(S3_SILVER_PATH)
        count = df.count()
        logger.info(f"✅ Parquet carregado: {count:,} registros, {len(df.columns)} colunas")

        # Log das colunas
        logger.info(f"Colunas: {', '.join(df.columns)}")

        return df

    except Exception as e:
        logger.error(f"❌ Erro ao ler S3: {e}")
        logger.error(traceback.format_exc())
        raise


def create_rds_engine(host, port, user, password, database):
    """Cria conexão SQLAlchemy para RDS."""
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"

    try:
        engine = create_engine(connection_string, echo=False)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Conexão RDS validada")

        return engine

    except Exception as e:
        logger.error(f"❌ Erro ao conectar RDS: {e}")
        logger.error(traceback.format_exc())
        raise


def create_rds_table_if_not_exists(engine, schema: str, table_name: str):
    """Cria tabela no RDS se não existir."""
    logger.info(f"Verificando tabela {schema}.{table_name}...")

    create_table_sql = f"""
    CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
        -- Identificadores
        "Número" VARCHAR(50) PRIMARY KEY,
        "Incidente_Pai" VARCHAR(50),
        "Aberto_por" VARCHAR(100),
        "Item_de_configuração" VARCHAR(255),

        -- Dimensões
        "Prioridade" VARCHAR(50),
        "Prioridade_Num" INT,
        "Produto" VARCHAR(100),
        "Categoria" VARCHAR(100),
        "Subcategoria" VARCHAR(100),
        "Grupo_designado" VARCHAR(100),
        "Descrição_resumida" TEXT,

        -- Timestamps
        "Aberto" TIMESTAMP,
        "Resolvido" TIMESTAMP,
        "Encerrado" TIMESTAMP,

        -- Features
        "Exige_Intervencao" INT,
        "Possui_Pai" INT,
        "Duracao_Horas" NUMERIC(10, 2),
        "Duração" NUMERIC(10, 2),
        "Data_Abertura" DATE,
        "Ano_Mes" VARCHAR(7),

        -- Targets (calculados pelo Glue)
        "KPI_Status_Int" INT,
        "Target_Risco_SLA" INT,

        -- Audit
        loaded_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """

    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
            logger.info(f"✅ Tabela {schema}.{table_name} pronta")

    except Exception as e:
        logger.error(f"⚠️  Erro ao criar tabela: {e}")
        # Não é fatal, tabela pode já existir


def truncate_rds_table(engine, schema: str, table_name: str):
    """Trunca tabela RDS (para reprocessamento)."""
    logger.info(f"Limpando tabela {schema}.{table_name}...")

    truncate_sql = f"TRUNCATE TABLE {schema}.{table_name};"

    try:
        with engine.connect() as conn:
            conn.execute(text(truncate_sql))
            conn.commit()
            logger.info(f"✅ Tabela {schema}.{table_name} truncada")

    except Exception as e:
        logger.error(f"⚠️  Erro ao truncar: {e}")


def load_dataframe_to_rds(df, engine, schema: str, table_name: str, batch_size: int = 10000):
    """Carrega DataFrame Spark → RDS em batches."""
    logger.info(f"Carregando DataFrame para RDS ({df.count():,} registros)...")

    total = df.count()

    # Converter para Pandas e enviar em batches
    pdf = df.toPandas()

    full_table_name = f"{schema}.{table_name}"

    try:
        pdf.to_sql(
            table_name,
            con=engine,
            schema=schema,
            if_exists='append',  # TRUNCATE executou antes
            index=False,
            chunksize=batch_size,
            method='multi'
        )
        logger.info(f"✅ {total:,} registros carregados com sucesso")

    except Exception as e:
        logger.error(f"❌ Erro ao carregar dados: {e}")
        logger.error(traceback.format_exc())
        raise


def create_rds_indexes(engine, schema: str, table_name: str):
    """Cria índices para performance."""
    logger.info(f"Criando índices em {schema}.{table_name}...")

    indexes = [
        {
            'name': f'idx_{table_name}_numero',
            'columns': '"Número"',
            'unique': False
        },
        {
            'name': f'idx_{table_name}_data_abertura',
            'columns': '"Data_Abertura"',
            'unique': False
        },
        {
            'name': f'idx_{table_name}_ano_mes',
            'columns': '"Ano_Mes"',
            'unique': False
        },
        {
            'name': f'idx_{table_name}_prioridade',
            'columns': '"Prioridade_Num"',
            'unique': False
        }
    ]

    try:
        with engine.connect() as conn:
            for idx in indexes:
                try:
                    create_idx_sql = f"""
                    CREATE INDEX IF NOT EXISTS {idx['name']}
                    ON {schema}.{table_name} ({idx['columns']});
                    """
                    conn.execute(text(create_idx_sql))
                    logger.info(f"  ✅ {idx['name']}")
                except Exception as e:
                    logger.warning(f"  ⚠️  {idx['name']}: {e}")

            conn.commit()
            logger.info("✅ Índices criados")

    except Exception as e:
        logger.error(f"❌ Erro ao criar índices: {e}")


def validate_load(engine, schema: str, table_name: str, expected_count: int):
    """Valida se dados foram carregados corretamente."""
    logger.info(f"Validando carga em {schema}.{table_name}...")

    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) as cnt FROM {schema}.{table_name};"))
            actual_count = result.scalar()

            if actual_count == expected_count:
                logger.info(f"✅ Validação OK: {actual_count:,} registros carregados")
                return True
            else:
                logger.warning(
                    f"⚠️  Contagem diferente: esperado {expected_count:,}, "
                    f"obtido {actual_count:,}"
                )
                return False

    except Exception as e:
        logger.error(f"❌ Erro na validação: {e}")
        return False


def log_summary(engine, schema: str, table_name: str):
    """Loga resumo da carga."""
    logger.info("=" * 70)
    logger.info(f"RESUMO DA CARGA - {schema}.{table_name}")
    logger.info("=" * 70)

    try:
        with engine.connect() as conn:
            # Contagem
            count_result = conn.execute(
                text(f"SELECT COUNT(*) as cnt FROM {schema}.{table_name};")
            )
            count = count_result.scalar()
            logger.info(f"Total de registros: {count:,}")

            # Distribuição por Ano_Mes
            dist_result = conn.execute(
                text(f"""
                SELECT "Ano_Mes", COUNT(*) as cnt
                FROM {schema}.{table_name}
                GROUP BY "Ano_Mes"
                ORDER BY "Ano_Mes";
                """)
            )
            logger.info("Distribuição por período:")
            for row in dist_result:
                logger.info(f"  {row[0]}: {row[1]:,}")

            # Data range
            range_result = conn.execute(
                text(f"""
                SELECT MIN("Data_Abertura"), MAX("Data_Abertura")
                FROM {schema}.{table_name};
                """)
            )
            min_date, max_date = range_result.first()
            logger.info(f"Período: {min_date} → {max_date}")

            # Null check
            null_result = conn.execute(
                text(f"""
                SELECT
                    COUNT(*) FILTER (WHERE "Número" IS NULL) as null_numero,
                    COUNT(*) FILTER (WHERE "Data_Abertura" IS NULL) as null_data
                FROM {schema}.{table_name};
                """)
            )
            null_numero, null_data = null_result.first()
            logger.info(f"Validação nulos: Número={null_numero}, Data_Abertura={null_data}")

    except Exception as e:
        logger.error(f"⚠️  Erro ao gerar summary: {e}")

    logger.info("=" * 70)


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Pipeline principal."""
    logger.info("🚀 Iniciando carga Silver S3 → RDS")
    logger.info(f"   S3 Input:  {S3_SILVER_PATH}")
    logger.info(f"   RDS Output: {RDS_SCHEMA}.{RDS_TABLE_NAME}")

    try:
        # 1. Ler S3
        df = read_silver_from_s3()
        total_records = df.count()

        # 2. Conectar RDS
        engine = create_rds_engine(RDS_HOST, RDS_PORT, RDS_USER, RDS_PASSWORD, RDS_DATABASE)

        # 3. Preparar tabela
        create_rds_table_if_not_exists(engine, RDS_SCHEMA, RDS_TABLE_NAME)
        truncate_rds_table(engine, RDS_SCHEMA, RDS_TABLE_NAME)

        # 4. Carregar dados
        load_dataframe_to_rds(df, engine, RDS_SCHEMA, RDS_TABLE_NAME, BATCH_SIZE)

        # 5. Criar índices
        create_rds_indexes(engine, RDS_SCHEMA, RDS_TABLE_NAME)

        # 6. Validar
        is_valid = validate_load(engine, RDS_SCHEMA, RDS_TABLE_NAME, total_records)

        # 7. Resumo
        log_summary(engine, RDS_SCHEMA, RDS_TABLE_NAME)

        if is_valid:
            logger.info("✅ Carga concluída com sucesso!")
            return 0
        else:
            logger.warning("⚠️  Carga concluída com alertas")
            return 1

    except Exception as e:
        logger.error(f"❌ Erro fatal: {e}")
        logger.error(traceback.format_exc())
        return 1

    finally:
        spark.stop()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
