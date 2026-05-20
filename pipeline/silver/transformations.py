"""
Feature engineering e transformações para Silver
"""
from pyspark.sql import functions as F


def create_all_features(df):
    """Cria 6 features derivadas para modelagem ML."""

    # 1. Exige_Intervencao: Status em aberto ou pendente
    df = df.withColumn(
        'Exige_Intervencao',
        F.when(F.col('Status').isin(['Aberto', 'Pendente']), 1).otherwise(0)
    )

    # 2. Prioridade_Num: Converte prioridade para numérica
    df = df.withColumn(
        'Prioridade_Num',
        F.when(F.col('Prioridade') == 'Crítica', 4)
         .when(F.col('Prioridade') == 'Alta', 3)
         .when(F.col('Prioridade') == 'Média', 2)
         .otherwise(1)
    )

    # 3. Possui_Pai: Se incidente tem pai
    df = df.withColumn(
        'Possui_Pai',
        F.when(F.col('Incidente_Pai').isNotNull(), 1).otherwise(0)
    )

    # 4. Duracao_Horas: Converte duração para horas
    df = df.withColumn(
        'Duracao_Horas',
        F.when(F.col('Duração').isNotNull(), F.col('Duração') / 60.0).otherwise(0)
    )

    # 5. Data_Abertura: Extrai data
    df = df.withColumn(
        'Data_Abertura',
        F.to_date(F.col('Aberto'))
    )

    # 6. Ano_Mes: Particiona por ano-mês
    df = df.withColumn(
        'Ano_Mes',
        F.date_format(F.col('Data_Abertura'), 'yyyy-MM')
    )

    # 7. KPI_Status_Int: Converte KPI_Violado para inteiro
    df = df.withColumn(
        'KPI_Status_Int',
        F.when(F.col('KPI_Violado') == True, 1).otherwise(0)
    )

    return df


def handle_nulls(df):
    """Trata valores nulos conforme regras de negócio."""
    fillna_rules = {
        'Produto': 'Não Classificado',
        'Categoria': 'Não Classificado',
        'Subcategoria': 'Não Informada',
        'Incidente_Pai': 'Independente',
        'Código_de_fechamento': 'Não Encerrado',
        'Solução': 'Sem Descrição'
    }

    for col, fill_value in fillna_rules.items():
        if col in df.columns:
            df = df.fillna({col: fill_value})

    df = df.fillna({'Resolvido': F.col('Aberto'), 'Encerrado': F.col('Aberto')})
    df = df.fillna(0)

    return df


def calculate_target_risco_sla(df):
    """Calcula target de risco de SLA em 3 camadas."""

    df = df.withColumn(
        'Target_Risco_SLA_L1',
        F.when(F.col('KPI_Violado') == True, 1).otherwise(0)
    )

    df = df.withColumn(
        'Target_Risco_SLA_L2',
        F.when(F.col('Prioridade').isin(['Crítica', 'Alta']), 1).otherwise(0)
    )

    df = df.withColumn(
        'Target_Risco_SLA_L3',
        F.when(F.col('Duracao_Horas') > 8, 1).otherwise(0)
    )

    df = df.withColumn(
        'Target_Risco_SLA',
        F.when(
            (F.col('Target_Risco_SLA_L1') == 1) |
            (F.col('Target_Risco_SLA_L2') == 1) |
            (F.col('Target_Risco_SLA_L3') == 1),
            1
        ).otherwise(0)
    )

    return df.drop('Target_Risco_SLA_L1', 'Target_Risco_SLA_L2', 'Target_Risco_SLA_L3')
