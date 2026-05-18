"""
Testes unitários para transformações Silver
Valida lógica de features e targets sem necessidade de Glue/Spark cluster

Executar: pytest pipeline/silver/test_transformations.py -v
"""

import pytest
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, TimestampType
from datetime import datetime, timedelta

from transformations import (
    feature_exige_intervencao,
    feature_prioridade_numerica,
    feature_possui_pai,
    feature_duracao_horas,
    feature_data_abertura,
    feature_ano_mes,
    feature_kpi_status_int,
    handle_nulls,
    calculate_target_risco_sla
)


@pytest.fixture(scope="session")
def spark():
    """Cria SparkSession para testes."""
    return SparkSession.builder \
        .appName("test-silver-transformations") \
        .master("local[1]") \
        .getOrCreate()


@pytest.fixture
def sample_data(spark):
    """Cria DataFrame de exemplo para testes."""
    data = [
        ("INC001", "P1", "Servidor", "Performance", "CPU", "TI",
         "2025-01-15 08:00:00", "2025-01-15 09:00:00", "2025-01-15 10:00:00",
         3600, "Aberto", "SIM", "SIM", None, "Reiniciado", "Solução rápida"),
        ("INC002", "P2", None, "Rede", "Conexão", "TI",
         "2025-02-20 14:00:00", "2025-02-20 18:00:00", "2025-02-20 20:00:00",
         21600, "Sem Intervenção", "NAO", "NAO", "INC001", None, None),
        ("INC003", "P3", "BD", "Banco de Dados", None, "DBA",
         "2025-03-10 10:00:00", None, None,
         86400, "Aberto", "SIM", None, None, "Aguardando", "Problema complexo"),
    ]

    schema = StructType([
        StructField("Número", StringType()),
        StructField("Prioridade", StringType()),
        StructField("Produto", StringType()),
        StructField("Categoria", StringType()),
        StructField("Subcategoria", StringType()),
        StructField("Grupo_designado", StringType()),
        StructField("Aberto", StringType()),
        StructField("Resolvido", StringType()),
        StructField("Encerrado", StringType()),
        StructField("Duração", IntegerType()),
        StructField("Status", StringType()),
        StructField("Entrou_para_KPI", StringType()),
        StructField("KPI_Violado", StringType()),
        StructField("Incidente_Pai", StringType()),
        StructField("Código_de_fechamento", StringType()),
        StructField("Solução", StringType()),
    ])

    return spark.createDataFrame(data, schema=schema)


# === TESTES DE FEATURES ===

class TestFeatureExigeIntervencao:
    """Testes para feature de esforço real vs. ruído."""

    def test_exige_intervencao_aberto(self, spark, sample_data):
        """Status 'Aberto' deve resultar em 1."""
        result = feature_exige_intervencao(sample_data)
        assert result.filter(result.Número == "INC001").select("Exige_Intervencao").collect()[0][0] == 1

    def test_exige_intervencao_sem_intervencao(self, spark, sample_data):
        """Status 'Sem Intervenção' deve resultar em 0."""
        result = feature_exige_intervencao(sample_data)
        assert result.filter(result.Número == "INC002").select("Exige_Intervencao").collect()[0][0] == 0

    def test_exige_intervencao_todos_preenchidos(self, spark, sample_data):
        """Todos os registros devem ter a feature preenchida."""
        result = feature_exige_intervencao(sample_data)
        nulls = result.filter(result.Exige_Intervencao.isNull()).count()
        assert nulls == 0


class TestFeaturePrioridadeNumerica:
    """Testes para conversão de prioridade texto → número."""

    def test_prioridade_p1(self, spark, sample_data):
        """P1 deve ser convertido para 1."""
        result = feature_prioridade_numerica(sample_data)
        assert result.filter(result.Número == "INC001").select("Prioridade_Num").collect()[0][0] == 1

    def test_prioridade_p2(self, spark, sample_data):
        """P2 deve ser convertido para 2."""
        result = feature_prioridade_numerica(sample_data)
        assert result.filter(result.Número == "INC002").select("Prioridade_Num").collect()[0][0] == 2

    def test_prioridade_p3(self, spark, sample_data):
        """P3 deve ser convertido para 3."""
        result = feature_prioridade_numerica(sample_data)
        assert result.filter(result.Número == "INC003").select("Prioridade_Num").collect()[0][0] == 3


class TestFeaturePossuiPai:
    """Testes para identificação de incidentes vinculados."""

    def test_possui_pai_sim(self, spark, sample_data):
        """INC002 tem pai (INC001) → deve ser 1."""
        result = feature_possui_pai(sample_data)
        assert result.filter(result.Número == "INC002").select("Possui_Pai").collect()[0][0] == 1

    def test_possui_pai_nao(self, spark, sample_data):
        """INC001 não tem pai → deve ser 0."""
        result = feature_possui_pai(sample_data)
        assert result.filter(result.Número == "INC001").select("Possui_Pai").collect()[0][0] == 0


class TestFeatureDuracaoHoras:
    """Testes para conversão de duração segundos → horas."""

    def test_duracao_1hora(self, spark, sample_data):
        """3600 segundos = 1.0 hora."""
        result = feature_duracao_horas(sample_data)
        duracao = result.filter(result.Número == "INC001").select("Duracao_Horas").collect()[0][0]
        assert abs(duracao - 1.0) < 0.01

    def test_duracao_6horas(self, spark, sample_data):
        """21600 segundos = 6.0 horas."""
        result = feature_duracao_horas(sample_data)
        duracao = result.filter(result.Número == "INC002").select("Duracao_Horas").collect()[0][0]
        assert abs(duracao - 6.0) < 0.01

    def test_duracao_24horas(self, spark, sample_data):
        """86400 segundos = 24.0 horas."""
        result = feature_duracao_horas(sample_data)
        duracao = result.filter(result.Número == "INC003").select("Duracao_Horas").collect()[0][0]
        assert abs(duracao - 24.0) < 0.01


class TestFeatureAnoMes:
    """Testes para criação de coluna de partição."""

    def test_ano_mes_2025_01(self, spark, sample_data):
        """INC001 (2025-01-15) deve gerar 2025-01."""
        result = feature_ano_mes(sample_data)
        ano_mes = result.filter(result.Número == "INC001").select("Ano_Mes").collect()[0][0]
        assert ano_mes == "2025-01"

    def test_ano_mes_2025_02(self, spark, sample_data):
        """INC002 (2025-02-20) deve gerar 2025-02."""
        result = feature_ano_mes(sample_data)
        ano_mes = result.filter(result.Número == "INC002").select("Ano_Mes").collect()[0][0]
        assert ano_mes == "2025-02"


class TestFeatureKPIStatusInt:
    """Testes para normalização de KPI_Violado."""

    def test_kpi_sim(self, spark, sample_data):
        """KPI_Violado 'SIM' → 1."""
        result = feature_kpi_status_int(sample_data)
        status = result.filter(result.Número == "INC001").select("KPI_Status_Int").collect()[0][0]
        assert status == 1

    def test_kpi_nao(self, spark, sample_data):
        """KPI_Violado 'NAO' → 0."""
        result = feature_kpi_status_int(sample_data)
        status = result.filter(result.Número == "INC002").select("KPI_Status_Int").collect()[0][0]
        assert status == 0

    def test_kpi_null(self, spark, sample_data):
        """KPI_Violado NULL → -1."""
        result = feature_kpi_status_int(sample_data)
        status = result.filter(result.Número == "INC003").select("KPI_Status_Int").collect()[0][0]
        assert status == -1


# === TESTES DE TARGETS ===

class TestTargetRiscoSLA:
    """Testes para cálculo de target de risco SLA (3 camadas)."""

    def test_target_base_violado(self, spark, sample_data):
        """Layer 1: KPI_Status_Int=1 → Target=1."""
        df = feature_exige_intervencao(sample_data) \
            .transform(feature_prioridade_numerica) \
            .transform(feature_duracao_horas) \
            .transform(feature_kpi_status_int) \
            .transform(feature_possui_pai)

        result = calculate_target_risco_sla(df)
        target = result.filter(result.Número == "INC001").select("Target_Risco_SLA").collect()[0][0]
        assert target == 1

    def test_target_base_ok(self, spark, sample_data):
        """Layer 1: KPI_Status_Int=0 → Target=0."""
        df = feature_exige_intervencao(sample_data) \
            .transform(feature_prioridade_numerica) \
            .transform(feature_duracao_horas) \
            .transform(feature_kpi_status_int) \
            .transform(feature_possui_pai)

        result = calculate_target_risco_sla(df)
        target = result.filter(result.Número == "INC002").select("Target_Risco_SLA").collect()[0][0]
        assert target == 0

    def test_target_isencao_pai(self, spark, sample_data):
        """Layer 3: Possui_Pai=1 → sempre Target=0."""
        df = feature_exige_intervencao(sample_data) \
            .transform(feature_prioridade_numerica) \
            .transform(feature_duracao_horas) \
            .transform(feature_kpi_status_int) \
            .transform(feature_possui_pai)

        result = calculate_target_risco_sla(df)
        # INC002 tem pai, então target deve ser 0
        target = result.filter(result.Número == "INC002").select("Target_Risco_SLA").collect()[0][0]
        assert target == 0


# === TESTES DE NULOS ===

class TestHandleNulls:
    """Testes para tratamento de valores nulos."""

    def test_produto_null_filled(self, spark, sample_data):
        """Produto nulo deve ser preenchido com 'Não Classificado'."""
        result = handle_nulls(sample_data)
        produto = result.filter(result.Número == "INC002").select("Produto").collect()[0][0]
        assert produto == "Não Classificado"

    def test_categoria_null_filled(self, spark, sample_data):
        """Categoria nula deve ser preenchida com 'Não Classificado'."""
        result = handle_nulls(sample_data)
        categoria = result.filter(result.Número == "INC003").select("Categoria").collect()[0][0]
        assert categoria == "Não Classificado"

    def test_nulos_removidos_completos(self, spark, sample_data):
        """Após handle_nulls, Produto, Categoria, Subcategoria não devem ter nulos."""
        result = handle_nulls(sample_data)
        nulls = result.filter(
            result.Produto.isNull() |
            result.Categoria.isNull() |
            result.Subcategoria.isNull()
        ).count()
        assert nulls == 0


# === TESTES DE INTEGRAÇÃO ===

class TestPipelineIntegration:
    """Testes de pipeline completo."""

    def test_pipeline_all_features(self, spark, sample_data):
        """Testa criação de todas as features em sequência."""
        result = sample_data \
            .transform(feature_exige_intervencao) \
            .transform(feature_prioridade_numerica) \
            .transform(feature_possui_pai) \
            .transform(feature_duracao_horas) \
            .transform(feature_data_abertura) \
            .transform(feature_ano_mes) \
            .transform(feature_kpi_status_int)

        expected_cols = [
            'Exige_Intervencao', 'Prioridade_Num', 'Possui_Pai',
            'Duracao_Horas', 'Data_Abertura', 'Ano_Mes', 'KPI_Status_Int'
        ]

        for col in expected_cols:
            assert col in result.columns

    def test_pipeline_count_unchanged(self, spark, sample_data):
        """Features não devem alterar número de registros."""
        original_count = sample_data.count()

        result = sample_data \
            .transform(feature_exige_intervencao) \
            .transform(feature_prioridade_numerica) \
            .transform(feature_possui_pai) \
            .transform(feature_duracao_horas)

        assert result.count() == original_count
