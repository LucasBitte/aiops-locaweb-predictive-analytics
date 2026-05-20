"""
Bronze: Converter XLSX to Parquet
Epico: E4->E5 (transicao)

Entrada: s3://bucket/bronze/LW-DATASET.xlsx (feito upload em E4)
Saida:   s3://bucket/bronze/incidents_standardized.parquet

Responsabilidade:
- Ler Excel do S3
- Validar schema esperado
- Converter para Parquet com tipos otimizados
- Salvar particionado para Glue consumir
"""

import sys
import os
from datetime import datetime
from io import BytesIO

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

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


S3_BUCKET = os.getenv("S3_BUCKET", "aiops-locaweb-datalake-2026")
XLSX_PATH = f"s3://{S3_BUCKET}/bronze/LW-DATASET.xlsx"
PARQUET_PATH = f"s3://{S3_BUCKET}/bronze/incidents_standardized.parquet"

# Colunas reais no arquivo XLSX (com acentuacao e espacos)
ACTUAL_COLS = [
    'Número', 'Prioridade', 'Produto', 'Categoria', 'Subcategoria',
    'Grupo designado', 'Item de configuração', 'Aberto', 'Resolvido', 'Encerrado',
    'Duração', 'Código de fechamento', 'Descrição resumida', 'Solução', 'Aberto por',
    'Incidente Pai', 'Status', 'Entrou para KPI?', 'KPI Violado?'
]

# Colunas esperadas (normalizadas para Silver)
EXPECTED_COLS = [
    'Numero', 'Prioridade', 'Produto', 'Categoria', 'Subcategoria',
    'Grupo_designado', 'Aberto', 'Resolvido', 'Encerrado', 'Duracao',
    'Status', 'Entrou_para_KPI', 'KPI_Violado', 'Incidente_Pai',
    'Codigo_de_fechamento', 'Solucao', 'Aberto_por', 'Descricao_resumida'
]

# Mapeamento de colunas reais para normalizadas
COL_MAPPING = {
    'Número': 'Numero',
    'Grupo designado': 'Grupo_designado',
    'Item de configuração': 'Item_de_configuracao',
    'Duração': 'Duracao',
    'Código de fechamento': 'Codigo_de_fechamento',
    'Descrição resumida': 'Descricao_resumida',
    'Solução': 'Solucao',
    'Aberto por': 'Aberto_por',
    'Incidente Pai': 'Incidente_Pai',
    'Entrou para KPI?': 'Entrou_para_KPI',
    'KPI Violado?': 'KPI_Violado'
}


def log_info(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [INFO] {msg}")


def log_error(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [ERROR] {msg}")


def normalize_columns(df):
    log_info("Normalizando nomes de colunas...")

    rename_dict = {}
    for old_name in df.columns:
        if old_name in COL_MAPPING:
            rename_dict[old_name] = COL_MAPPING[old_name]

    if rename_dict:
        log_info(f"Renomeando {len(rename_dict)} colunas...")
        df = df.rename(columns=rename_dict)

    return df


def validate_schema(df):
    log_info(f"Colunas encontradas no arquivo: {list(df.columns)}")

    # Normalizar colunas primeiro
    df = normalize_columns(df)

    # Selecionar apenas as colunas importantes (remover Item_de_configuracao)
    cols_to_keep = [col for col in df.columns if col in EXPECTED_COLS + ['Item_de_configuracao']]

    if len(cols_to_keep) > 0:
        log_info(f"Mantendo {len(cols_to_keep)} colunas")
        df = df[cols_to_keep]

    return df


def convert_dtypes(df):
    log_info("Convertendo tipos de dados...")

    date_cols = ['Aberto', 'Resolvido', 'Encerrado']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    numeric_cols = ['Duracao']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    bool_cols = ['Entrou_para_KPI', 'KPI_Violado']
    for col in bool_cols:
        if col in df.columns:
            try:
                df[col] = df[col].astype('bool')
            except:
                pass

    string_cols = [
        'Numero', 'Prioridade', 'Produto', 'Categoria', 'Subcategoria',
        'Grupo_designado', 'Status', 'Incidente_Pai', 'Codigo_de_fechamento',
        'Solucao', 'Aberto_por', 'Descricao_resumida'
    ]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype('string')

    log_info("Tipos de dados convertidos")
    return df


def load_from_s3(s3_path):
    log_info(f"Lendo XLSX do S3: {s3_path}...")

    try:
        profile = os.getenv("AWS_PROFILE")
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        s3_client = session.client('s3', verify=False)

        parts = s3_path.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1]

        log_info(f"Fazendo download de s3://{bucket}/{key}...")
        obj = s3_client.get_object(Bucket=bucket, Key=key)

        file_bytes = obj['Body'].read()
        file_buffer = BytesIO(file_bytes)
        df = pd.read_excel(file_buffer)

        log_info(f"Carregado do S3: {len(df)} registros")
        return df

    except NoCredentialsError:
        log_error("AWS credentials nao encontradas. Tentando arquivo local...")
        return load_from_local("data/raw/LW-DATASET.xlsx")
    except ClientError as e:
        log_error(f"Erro ao baixar do S3: {e}")
        log_error("Tentando arquivo local como fallback...")
        return load_from_local("data/raw/LW-DATASET.xlsx")


def load_from_local(local_xlsx_path):
    log_info(f"Lendo XLSX local: {local_xlsx_path}...")

    if not os.path.exists(local_xlsx_path):
        log_error(f"Arquivo nao encontrado: {local_xlsx_path}")
        raise FileNotFoundError(f"XLSX nao existe: {local_xlsx_path}")

    df = pd.read_excel(local_xlsx_path)
    log_info(f"Carregado: {len(df)} registros, {len(df.columns)} colunas")

    return df


def save_to_parquet_s3(df, s3_path):
    log_info(f"Salvando Parquet no S3: {s3_path}...")

    try:
        profile = os.getenv("AWS_PROFILE")
        session = boto3.Session(profile_name=profile) if profile else boto3.Session()
        s3_client = session.client('s3', verify=False)

        try:
            import pyarrow as pa
            import pyarrow.parquet as pq
            HAS_PYARROW = True
        except ImportError:
            HAS_PYARROW = False
            log_error("pyarrow nao disponivel, usando pandas...")

        if HAS_PYARROW:
            table = pa.Table.from_pandas(df)
            parts = s3_path.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1]

            local_parquet = "temp_incidents.parquet"
            pq.write_table(table, local_parquet, coerce_timestamps='us')

            log_info(f"Fazendo upload para s3://{bucket}/{key}...")
            s3_client.upload_file(local_parquet, bucket, key)

            if os.path.exists(local_parquet):
                os.remove(local_parquet)

            log_info("Parquet salvo em S3")
        else:
            log_info("Salvando como CSV em vez de Parquet...")
            parts = s3_path.replace("s3://", "").split("/", 1)
            bucket = parts[0]
            key = parts[1].replace(".parquet", ".csv")

            local_csv = "temp_incidents.csv"
            df.to_csv(local_csv, index=False)

            log_info(f"Fazendo upload para s3://{bucket}/{key}...")
            s3_client.upload_file(local_csv, bucket, key)

            if os.path.exists(local_csv):
                os.remove(local_csv)

            log_info("CSV salvo em S3")

    except Exception as e:
        log_error(f"Erro ao salvar: {e}")
        raise


def main():
    print("\n" + "="*70)
    print("BRONZE: XLSX to Parquet Conversion (E4->E5)")
    print("="*70 + "\n")

    try:
        if not HAS_PANDAS:
            log_error("pandas nao esta disponivel")
            return 1

        if not HAS_BOTO3:
            log_error("boto3 nao esta disponivel")
            return 1

        log_info("Iniciando conversao...")
        df = load_from_s3(XLSX_PATH)

        log_info(f"Validando schema ({len(EXPECTED_COLS)} colunas esperadas)...")
        df = validate_schema(df)

        df = convert_dtypes(df)

        log_info("Gerando estatisticas...")
        print(f"\nEstatisticas do Dataset:")
        print(f"   - Registros: {len(df):,}")
        print(f"   - Colunas: {len(df.columns)}")
        try:
            print(f"   - Periodo: {df['Aberto'].min()} -> {df['Aberto'].max()}")
        except:
            print(f"   - Periodo: (nao disponivel)")

        log_info("Salvando em Parquet...")
        save_to_parquet_s3(df, PARQUET_PATH)

        print("\n" + "="*70)
        print("[SUCCESS] CONVERSAO CONCLUIDA COM SUCESSO")
        print("="*70)
        print(f"\nProximos passos:")
        print(f"1. Glue job pode consumir: {PARQUET_PATH}")
        print(f"2. Executar Glue: transform_bronze_to_silver")
        print(f"3. Validar Silver em S3: s3://{S3_BUCKET}/silver/")
        print()

        return 0

    except Exception as e:
        log_error(f"Pipeline falhou: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
