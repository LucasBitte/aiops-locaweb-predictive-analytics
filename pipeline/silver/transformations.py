"""
Módulo de transformações reutilizáveis para Bronze → Silver
Contém lógica de feature engineering e cálculos de targets
"""

from pyspark.sql import functions as F
from pyspark.sql.types import IntegerType, DoubleType
from config import FILLNA_RULES


def feature_exige_intervencao(df):
    """
    Cria flag de esforço real vs. ruído de monitoramento.
    1 = incidente que exigiu intervenção (Status != 'Sem Intervenção')
    0 = incidente de monitoramento apenas
    """
    return df.withColumn(
        'Exige_Intervencao',
        F.when(F.col('Status') != 'Sem Intervenção', 1).otherwise(0)
    )


def feature_prioridade_numerica(df):
    """
    Extrai número de prioridade (P1-P5 → 1-5).
    Facilita operações numéricas e modelos de ML.
    """
    return df.withColumn(
        'Prioridade_Num',
        F.substring(F.col('Prioridade'), 1, 1).cast(IntegerType())
    )


def feature_possui_pai(df):
    """
    Identifica incidentes vinculados a um incidente pai.
    1 = tem pai (incidente relacionado)
    0 = incidente independente
    """
    return df.withColumn(
        'Possui_Pai',
        F.when(F.col('Incidente_Pai').isNotNull(), 1).otherwise(0)
    )


def feature_duracao_horas(df):
    """
    Converte duração de segundos para horas (formato decimal).
    Mais legível para análise de SLA.
    """
    return df.withColumn(
        'Duracao_Horas',
        (F.col('Duração') / 3600).cast(DoubleType())
    )


def feature_data_abertura(df):
    """
    Extrai data de abertura (sem hora) para agregações diárias.
    """
    return df.withColumn(
        'Data_Abertura',
        F.to_date(F.col('Aberto'))
    )


def feature_ano_mes(df):
    """
    Cria coluna de partição (yyyy-MM).
    Usada para particionamento eficiente em S3.
    """
    return df.withColumn(
        'Ano_Mes',
        F.date_format(F.col('Aberto'), 'yyyy-MM')
    )


def feature_kpi_status_int(df):
    """
    Normaliza KPI_Violado (texto) para inteiro.
    SIM → 1 (violado)
    NAO → 0 (atendido)
    NULL → -1 (desconhecido)
    """
    return df.withColumn(
        'KPI_Status_Int',
        F.when(F.col('KPI_Violado') == 'SIM', 1)
         .when(F.col('KPI_Violado') == 'NAO', 0)
         .otherwise(-1)
    )


def create_all_features(df):
    """
    Cria todas as 6 features derivadas em sequência.
    Retorna DataFrame com colunas originais + engineered.
    """
    return (df
            .transform(feature_exige_intervencao)
            .transform(feature_prioridade_numerica)
            .transform(feature_possui_pai)
            .transform(feature_duracao_horas)
            .transform(feature_data_abertura)
            .transform(feature_ano_mes)
            .transform(feature_kpi_status_int))


def handle_nulls(df):
    """
    Trata valores nulos conforme regras de negócio.
    Define valores padrão seguindo políticas de preenchimento.
    """
    for col, fill_value in FILLNA_RULES.items():
        if col in df.columns:
            df = df.withColumn(col, F.coalesce(F.col(col), F.lit(fill_value)))

    return df


def calculate_target_risco_sla(df):
    """
    Calcula target para modelo de risco de SLA (3 camadas).

    Layer 1 (Base): KPI_Status_Int = 1 → violado
    Layer 2 (Heurística): P2 + duração > 4h + KPI desconhecido → força violação
    Layer 3 (Isenção): incidente com pai ou sem intervenção → sempre OK
    """
    # Layer 1: Base (KPI oficial)
    df = df.withColumn(
        'Target_Risco_SLA',
        F.when(F.col('KPI_Status_Int') == 1, 1).otherwise(0)
    )

    # Layer 2: Heurística (detecta violações não registradas)
    df = df.withColumn(
        'Target_Risco_SLA',
        F.when(
            (F.col('KPI_Status_Int') == -1) &  # KPI desconhecido
            (F.col('Prioridade_Num') == 2) &   # P2 (4h SLA)
            (F.col('Duracao_Horas') > 4),      # Passou do SLA
            1
        ).otherwise(F.col('Target_Risco_SLA'))
    )

    # Layer 3: Isenção (incidentes com pai ou sem intervenção sempre OK)
    df = df.withColumn(
        'Target_Risco_SLA',
        F.when(
            (F.col('Possui_Pai') == 1) |           # Tem incidente pai
            (F.col('Exige_Intervencao') == 0),     # Sem intervenção
            0
        ).otherwise(F.col('Target_Risco_SLA'))
    )

    return df
