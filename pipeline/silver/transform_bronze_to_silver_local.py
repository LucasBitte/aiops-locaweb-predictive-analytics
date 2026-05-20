"""
Transformacao Bronze to Silver (Local com Pandas)
Lê Parquet do S3, aplica transformações, salva em Silver
Versão local - sem Spark/Glue, apenas Pandas
"""

import pandas as pd
import os
import traceback
from datetime import datetime
from io import BytesIO

try:
    import boto3
    from botocore.exceptions import NoCredentialsError, ClientError
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import pyarrow.parquet as pq
    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


BRONZE_PATH = "s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet"
SILVER_PATH = "s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet"
MIN_DATE = "2025-01-01"


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


def handle_nulls(df):
    log_info("Tratando valores nulos...")

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
            df[col] = df[col].fillna(val)

    return df


def create_features(df):
    log_info("Criando features de engenharia...")

    df['Data_Abertura'] = pd.to_datetime(df['Aberto'])
    df['Ano_Mes'] = df['Data_Abertura'].dt.strftime('%Y-%m')

    df['Prioridade_Num'] = df['Prioridade'].map({
        '1 - Critica': 1,
        '2 - Alta': 2,
        '3 - Media': 3,
        '4 - Baixa': 4
    }).fillna(5)

    df['Exige_Intervencao'] = (
        (df['Entrou_para_KPI'] == True) |
        (df['Entrou_para_KPI'] == "Sim")
    ).astype(int)

    df['Possui_Pai'] = (df['Incidente_Pai'].notna()).astype(int)

    df['Duracao_Horas'] = df['Duracao'].astype(float) / 60.0

    log_info("Features criadas: Data_Abertura, Ano_Mes, Prioridade_Num, Exige_Intervencao, Possui_Pai, Duracao_Horas")
    return df


def calculate_target(df):
    log_info("Calculando Target_Risco_SLA...")

    df['Target_Risco_SLA'] = (
        (df['KPI_Violado'] == True) |
        (df['KPI_Violado'] == "Sim") |
        (df['Prioridade_Num'] <= 2) |
        (df['Duracao_Horas'] > 8)
    ).astype(int)

    return df


def filter_by_date(df, min_date):
    log_info(f"Filtrando registros a partir de {min_date}")

    df = df[df['Data_Abertura'] >= min_date]
    return df


def save_parquet_to_s3(df, s3_path):
    log_info(f"Salvando Parquet em S3: {s3_path}")

    try:
        profile = os.getenv("AWS_PROFILE")
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        s3_client = session.client("s3", verify=False)

        parts = s3_path.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        local_parquet = "temp_silver.parquet"

        log_info("Escrevendo Parquet localmente...")
        df.to_parquet(local_parquet, index=False, engine='pyarrow')

        log_info(f"Fazendo upload para s3://{bucket}/{key}...")
        s3_client.upload_file(local_parquet, bucket, key)

        if os.path.exists(local_parquet):
            os.remove(local_parquet)

        log_info("Parquet salvo em S3")

    except Exception as e:
        log_error(f"Erro ao salvar: {e}")
        raise


def main():
    log_section("TRANSFORMACAO BRONZE TO SILVER (LOCAL)")

    try:
        if not HAS_BOTO3:
            log_error("boto3 nao esta disponivel")
            return 1

        if not HAS_PYARROW:
            log_error("pyarrow nao esta disponivel")
            return 1

        # 1. Ler Bronze
        df = read_parquet_from_s3(BRONZE_PATH)

        # 2. Tratar nulos
        df = handle_nulls(df)

        # 3. Criar features
        df = create_features(df)

        # 4. Calcular target
        df = calculate_target(df)

        # 5. Filtrar por data
        min_date = pd.to_datetime(MIN_DATE)
        df = filter_by_date(df, min_date)

        registros_finais = len(df)
        if registros_finais == 0:
            log_error("DataFrame vazio após filtros!")
            return 1

        log_info(f"Registros para Silver: {registros_finais}")

        # 6. Salvar em Silver
        save_parquet_to_s3(df, SILVER_PATH)

        # 7. Relatorio final
        log_section("RESUMO DA EXECUCAO")
        log_info(f"Total de registros processados: {registros_finais}")
        log_info(f"Colunas finais: {len(df.columns)}")
        log_info(f"Particoes (Ano_Mes): {df['Ano_Mes'].nunique()}")
        log_info(f"Output: {SILVER_PATH}")

        print(f"\nTarget_Risco_SLA:")
        print(f"  Risco: {(df['Target_Risco_SLA'] == 1).sum()} registros")
        print(f"  Normal: {(df['Target_Risco_SLA'] == 0).sum()} registros")

        print(f"\nAmostra de dados (5 primeiros registros):")
        cols_amostra = ['Numero', 'Prioridade', 'Duracao_Horas', 'Target_Risco_SLA', 'Ano_Mes']
        print(df[cols_amostra].head().to_string())

        log_section("SUCESSO - TRANSFORMACAO CONCLUIDA")
        return 0

    except Exception as e:
        log_error(f"Pipeline falhou: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
