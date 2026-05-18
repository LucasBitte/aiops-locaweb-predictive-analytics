"""
Job Apache Glue: Transformação Bronze → Silver
Converte dados brutos do ITSM em dataset refinado para modelagem ML.

Entrada:  s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet
Saída:    s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet

Épico: E5 - Analytics Exploratória
Versão: 1.0
Data: 2026-05-18
"""

import sys
import traceback
from datetime import datetime

# Glue imports
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import functions as F

# Custom modules
from config import (
    BRONZE_PATH, SILVER_PATH, MIN_DATE, PARTITION_COLS,
    EXPECTED_SCHEMA_COLS
)
from transformations import (
    create_all_features, handle_nulls, calculate_target_risco_sla
)
from validators import (
    validate_schema, validate_not_empty, validate_critical_nulls,
    validate_silver_output, validate_partitions, ValidationError
)
from logger import GlueLogger


# === SETUP ===
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Logger centralizado
log = GlueLogger("AIOps-Silver-Glue")


def read_bronze():
    """Lê parquet do Bronze com otimizações Spark."""
    log.info("Iniciando leitura do Bronze...")
    try:
        df = spark.read.parquet(BRONZE_PATH)
        log.dataframe_info("✅ Bronze carregado", df)
        return df
    except Exception as e:
        log.error(f"Erro ao ler Bronze: {e}")
        raise


def filter_temporal(df, min_date=MIN_DATE):
    """Filtra apenas registros de 2025 em diante."""
    log.info(f"Filtrando registros >= {min_date}...")

    count_before = df.count()
    df_filtered = df.filter(F.col('Aberto') >= min_date)
    count_after = df_filtered.count()

    log.info(
        f"✅ Registros filtrados: {count_before:,} → {count_after:,} "
        f"({100 * (count_before - count_after) / count_before:.1f}% removido)"
    )
    return df_filtered


def create_features(df):
    """Cria 6 features derivadas para modelagem."""
    log.info("Criando 6 features derivadas...")
    df_featured = create_all_features(df)
    log.dataframe_info("✅ Features criadas", df_featured)
    return df_featured


def sanitize_nulls(df):
    """Trata valores nulos conforme regras de negócio."""
    log.info("Tratando valores nulos...")

    # Antes
    null_stats_before = validate_critical_nulls(df)
    log.dict_stats({"nulls_before": null_stats_before})

    # Aplicar regras
    df_clean = handle_nulls(df)

    # Depois
    null_stats_after = validate_critical_nulls(df_clean)
    log.dict_stats({"nulls_after": null_stats_after})

    log.info("✅ Nulos tratados conforme regras de negócio")
    return df_clean


def compute_targets(df):
    """Calcula targets para modelos ML (risco de SLA)."""
    log.info("Calculando Target_Risco_SLA (3 camadas)...")

    df_with_target = calculate_target_risco_sla(df)

    # Estatísticas de target
    total = df_with_target.count()
    violado = df_with_target.filter(F.col('Target_Risco_SLA') == 1).count()
    ok = total - violado

    log.dict_stats({
        'target_statistics': {
            'total': total,
            'violado': violado,
            'ok': ok,
            'violation_rate_percent': f"{100 * violado / total:.2f}%"
        }
    })

    log.info("✅ Target_Risco_SLA calculado")
    return df_with_target


def write_silver(df):
    """Escreve dataset Silver em S3 com partições."""
    log.info(f"Escrevendo Silver em {SILVER_PATH}...")

    try:
        # Escrever com particionamento
        df.write \
            .mode("overwrite") \
            .partitionBy("Ano_Mes") \
            .parquet(SILVER_PATH)

        log.dataframe_info("✅ Silver persistido", df)

        # Estatísticas de partição
        partitions = validate_partitions(df)
        log.info(f"Partições criadas: {sorted(partitions)}")

    except Exception as e:
        log.error(f"Erro ao escrever Silver: {e}")
        raise


def generate_quality_report(df, df_original):
    """Gera relatório de qualidade do Silver."""
    log.section("QUALITY REPORT")

    try:
        quality_stats = validate_silver_output(df)

        # Resumo geral
        log.dict_stats({
            'bronze_to_silver': {
                'records_input': df_original.count(),
                'records_output': df.count(),
                'records_filtered': df_original.count() - df.count(),
            },
            'effort_distribution': quality_stats['exige_intervencao'],
            'target_distribution': quality_stats['target_distribution'],
            'priority_distribution': quality_stats['prioridade_distribution'],
            'null_validation': quality_stats['critical_nulls']
        })

        log.info("✅ Relatório de qualidade gerado")
        return quality_stats

    except ValidationError as e:
        log.warning(f"⚠️  Validação levantou alerta: {e}")
        return None


# === MAIN PIPELINE ===
def main():
    """Executa pipeline completo Bronze → Silver."""
    try:
        log.section("INICIANDO JOB: transform_bronze_to_silver")
        log.info(f"Timestamp: {datetime.now().isoformat()}")

        # 1. Leitura
        df_bronze = read_bronze()
        df_original_count = df_bronze.count()

        # 2. Validações iniciais
        log.info("Validando schema do Bronze...")
        validate_schema(df_bronze, EXPECTED_SCHEMA_COLS)
        validate_not_empty(df_bronze)
        log.info("✅ Schema e conteúdo validados")

        # 3. Filtragem temporal
        df_filtered = filter_temporal(df_bronze)

        # 4. Feature engineering
        df_featured = create_features(df_filtered)

        # 5. Tratamento de nulos
        df_clean = sanitize_nulls(df_featured)

        # 6. Cálculo de targets
        df_final = compute_targets(df_clean)

        # 7. Persistência
        write_silver(df_final)

        # 8. Validação e relatório
        quality_report = generate_quality_report(df_final, df_bronze)

        # 9. Resumo final
        duration = log.elapsed_time()
        log.job_summary(df_original_count, df_final.count(), duration)

        log.section("✅ JOB CONCLUÍDO COM SUCESSO")

        return 0

    except ValidationError as e:
        log.error(f"Validação falhou: {e}")
        traceback.print_exc()
        job.commit()
        return 1

    except Exception as e:
        log.error(f"Pipeline falhou: {e}")
        traceback.print_exc()
        job.commit()
        return 1


if __name__ == "__main__":
    exit_code = main()
    job.commit()
    sys.exit(exit_code)
