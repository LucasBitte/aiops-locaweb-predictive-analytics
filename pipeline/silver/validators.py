"""
Validadores para Bronze e Silver
Garante qualidade de dados em cada etapa
"""

from pyspark.sql import functions as F
from config import EXPECTED_SCHEMA_COLS, MIN_RECORDS_SILVER, MAX_NULL_RATIO


class ValidationError(Exception):
    """Exceção customizada para validações de dados."""
    pass


def validate_schema(df, expected_cols=None):
    """
    Valida se as colunas esperadas existem no DataFrame.

    Args:
        df: PySpark DataFrame
        expected_cols: lista de colunas esperadas (default: EXPECTED_SCHEMA_COLS)

    Returns:
        True se válido, raises ValidationError caso contrário
    """
    if expected_cols is None:
        expected_cols = EXPECTED_SCHEMA_COLS

    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValidationError(
            f"Colunas faltantes no schema: {missing}\n"
            f"Esperadas: {expected_cols}\n"
            f"Presentes: {df.columns}"
        )

    return True


def validate_not_empty(df, min_records=100):
    """
    Valida se o DataFrame possui registros suficientes.

    Args:
        df: PySpark DataFrame
        min_records: mínimo de registros esperados

    Returns:
        True se válido, raises ValidationError caso contrário
    """
    count = df.count()
    if count < min_records:
        raise ValidationError(
            f"DataFrame vazio ou com poucos registros: {count} < {min_records}"
        )

    return True


def validate_critical_nulls(df, critical_cols=None):
    """
    Valida se colunas críticas possuem muitos nulos.

    Args:
        df: PySpark DataFrame
        critical_cols: colunas que não devem ter nulos (default: Prioridade, Status)

    Returns:
        Dict com estatísticas de nulos
    """
    if critical_cols is None:
        critical_cols = ['Prioridade', 'Status', 'Aberto']

    null_stats = {}
    for col in critical_cols:
        if col in df.columns:
            null_count = df.filter(F.col(col).isNull()).count()
            total = df.count()
            null_ratio = null_count / total if total > 0 else 0
            null_stats[col] = {
                'count': null_count,
                'ratio': null_ratio,
                'ok': null_count == 0
            }

    return null_stats


def validate_silver_output(df, min_records=MIN_RECORDS_SILVER):
    """
    Validação completa do output Silver.
    Verifica registros, nulos, distribuições.

    Args:
        df: PySpark DataFrame (Silver)
        min_records: mínimo esperado

    Returns:
        Dict com estatísticas de qualidade
    """
    total = df.count()

    if total < min_records:
        raise ValidationError(
            f"Silver com poucos registros: {total} < {min_records}"
        )

    # Estatísticas por feature
    stats = {
        'total_records': total,
        'exige_intervencao': {
            'with_effort': df.filter(F.col('Exige_Intervencao') == 1).count(),
            'without_effort': df.filter(F.col('Exige_Intervencao') == 0).count(),
        },
        'target_distribution': {
            'violado': df.filter(F.col('Target_Risco_SLA') == 1).count(),
            'ok': df.filter(F.col('Target_Risco_SLA') == 0).count(),
        },
        'prioridade_distribution': {},
        'critical_nulls': validate_critical_nulls(df)
    }

    # Distribuição por prioridade
    for priority in range(1, 6):
        count = df.filter(F.col('Prioridade_Num') == priority).count()
        stats['prioridade_distribution'][f'P{priority}'] = count

    return stats


def validate_partitions(df):
    """
    Valida se a coluna de partição (Ano_Mes) foi criada corretamente.

    Returns:
        Lista de partições criadas
    """
    partitions = df.select("Ano_Mes").distinct().collect()
    partition_values = [row[0] for row in partitions]

    if not partition_values:
        raise ValidationError("Nenhuma partição (Ano_Mes) foi criada!")

    return partition_values
