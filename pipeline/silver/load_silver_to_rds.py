"""
Carrega dados Silver (S3 Parquet) para RDS PostgreSQL
Para uso com dbt nas transformações Gold
"""

import pandas as pd
import os
import traceback
from datetime import datetime
from io import BytesIO
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Integer, Float, DateTime, Boolean
from sqlalchemy.types import VARCHAR, BIGINT, DOUBLE_PRECISION, TIMESTAMP, BOOLEAN

try:
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


SILVER_PATH = os.getenv("SILVER_PATH", "s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet")

RDS_HOST = os.getenv("RDS_HOST")
RDS_PORT = os.getenv("RDS_PORT", "5432")
RDS_USER = os.getenv("RDS_USER")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")
RDS_DATABASE = os.getenv("RDS_DATABASE")
RDS_SCHEMA = "public"
RDS_TABLE = "incidents_silver"

if not all([RDS_HOST, RDS_USER, RDS_PASSWORD, RDS_DATABASE]):
    log_error("Credenciais RDS não configuradas. Configure as variáveis de ambiente:")
    log_error("  RDS_HOST, RDS_USER, RDS_PASSWORD, RDS_DATABASE")
    exit(1)


def log_info(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [INFO] {msg}")


def log_error(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [ERROR] {msg}")


def log_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def read_parquet_from_s3(s3_path):
    log_info(f"Lendo Parquet do S3: {s3_path}")

    try:
        profile = os.getenv("AWS_PROFILE")
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        s3_client = session.client("s3", verify=False)

        parts = s3_path.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        log_info(f"Baixando de s3://{bucket}/{key}...")
        obj = s3_client.get_object(Bucket=bucket, Key=key)

        file_bytes = obj['Body'].read()
        df = pd.read_parquet(BytesIO(file_bytes))

        log_info(f"Carregado: {len(df)} registros, {len(df.columns)} colunas")
        return df

    except (NoCredentialsError, ClientError) as e:
        log_error(f"Erro ao baixar do S3: {e}")
        raise


def get_rds_connection():
    log_info(f"Conectando ao RDS: {RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}")

    try:
        connection_string = f"postgresql://{RDS_USER}:{RDS_PASSWORD}@{RDS_HOST}:{RDS_PORT}/{RDS_DATABASE}"
        engine = create_engine(connection_string)

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            log_info("Conexão com RDS estabelecida")

        return engine

    except Exception as e:
        log_error(f"Erro ao conectar ao RDS: {e}")
        raise


def create_table_if_not_exists(engine, df):
    log_info("Verificando/criando tabela no RDS...")

    col_types = {}
    for col in df.columns:
        dtype = df[col].dtype

        if 'datetime' in str(dtype):
            col_types[col] = TIMESTAMP()
        elif dtype == 'bool' or dtype == 'object' and df[col].dtype == 'bool':
            col_types[col] = BOOLEAN()
        elif 'int' in str(dtype):
            col_types[col] = BIGINT()
        elif 'float' in str(dtype):
            col_types[col] = DOUBLE_PRECISION()
        else:
            col_types[col] = VARCHAR(500)

    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {RDS_SCHEMA}.{RDS_TABLE}"))
        conn.commit()
        log_info(f"Tabela {RDS_TABLE} dropada (se existia)")

    df.to_sql(
        RDS_TABLE,
        engine,
        schema=RDS_SCHEMA,
        if_exists='replace',
        index=False,
        dtype=col_types,
        chunksize=1000
    )

    log_info(f"Tabela {RDS_TABLE} criada no schema {RDS_SCHEMA}")


def load_to_rds(engine, df):
    log_info(f"Carregando {len(df)} registros para RDS...")

    try:
        create_table_if_not_exists(engine, df)
        log_info(f"[SUCCESS] {len(df)} registros carregados para {RDS_TABLE}")
        return True

    except Exception as e:
        log_error(f"Erro ao carregar: {e}")
        raise


def main():
    log_section("CARREGAR SILVER PARA RDS")

    try:
        if not HAS_BOTO3:
            log_error("boto3 nao esta disponivel")
            return 1

        # 1. Ler Silver do S3
        df = read_parquet_from_s3(SILVER_PATH)

        # 2. Conectar ao RDS
        engine = get_rds_connection()

        # 3. Carregar para RDS
        load_to_rds(engine, df)

        # 4. Relatorio
        log_section("RESUMO")
        log_info(f"Registros carregados: {len(df)}")
        log_info(f"Colunas: {len(df.columns)}")
        log_info(f"Tabela RDS: {RDS_SCHEMA}.{RDS_TABLE}")
        log_info(f"Host: {RDS_HOST}:{RDS_PORT}")
        log_info(f"Database: {RDS_DATABASE}")

        print(f"\nProximos passos:")
        print(f"1. Configurar dbt/profiles.yml com host={RDS_HOST}")
        print(f"2. Executar: dbt run --select silver")
        print(f"3. Verificar dados em RDS:")
        print(f"   SELECT COUNT(*) FROM {RDS_SCHEMA}.{RDS_TABLE};")

        log_section("SUCESSO - CARREGAMENTO CONCLUIDO")
        return 0

    except Exception as e:
        log_error(f"Pipeline falhou: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
