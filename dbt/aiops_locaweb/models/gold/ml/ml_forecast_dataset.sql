{{ config(materialized='table') }}

/*
    Esse mart alimenta meu modelo de Forecast (Prophet/ARIMA).
    
    A transformação principal aqui é a mudança de granularidade:
    saio do nível de incidente individual e subo para o nível de DIA.
*/

WITH base AS (
    SELECT * FROM {{ ref('ml_base_features') }}
    -- Consumindo a Feature Store mestre que já possui o filtro Exige_Intervencao = TRUE
),

agregado_diario AS (
    SELECT
        -- Minha âncora temporal — uma linha por dia
        data_abertura,

        -- Variáveis de calendário para o modelo capturar sazonalidade.
        dia_semana_num,
        semana_ano,
        mes_abertura,
        trimestre,
        ano_mes,

        -- Flag de fim de semana
        MAX(abriu_fim_de_semana)                AS is_fim_de_semana,

        -- ─────────────────────────────────────────────
        -- Volume total — minha variável target do forecast
        -- ─────────────────────────────────────────────
        COUNT(*)                                AS total_chamados,

        -- Breakdowns por prioridade (Requisito obrigatório do desafio: P2 e P3)
        SUM(CASE WHEN prioridade_num = 1 THEN 1 ELSE 0 END)                  AS total_p1,
        SUM(CASE WHEN prioridade_num = 2 THEN 1 ELSE 0 END)                  AS total_p2,
        SUM(CASE WHEN prioridade_num = 3 THEN 1 ELSE 0 END)                  AS total_p3,
        SUM(CASE WHEN prioridade_num = 4 THEN 1 ELSE 0 END)                  AS total_p4,

        -- Volume de críticos (P1+P2) como métrica consolidada
        SUM(CASE WHEN prioridade_num <= 2 THEN 1 ELSE 0 END)                  AS total_criticos,

        -- Violações de SLA no dia
        SUM(target_risco_sla)                   AS total_violacoes_sla,

        -- Taxa diária de violação normalizada
        ROUND(
            SUM(target_risco_sla)::numeric /
            NULLIF(COUNT(*), 0) * 100, 2
        )                                       AS pct_violacao_sla,

        -- Pressão operacional do dia
        SUM(score_risco_operacional)            AS pressao_operacional_dia,
        AVG(score_risco_operacional)            AS score_risco_medio_dia,

        -- Tempo médio de resolução no dia
        ROUND(AVG(horas_ate_resolucao)::numeric, 2) AS media_horas_resolucao

    FROM base
    GROUP BY
        data_abertura,
        dia_semana_num,
        semana_ano,
        mes_abertura,
        trimestre,
        ano_mes
)

SELECT * FROM agregado_diario
-- Ordeno cronologicamente porque os modelos de série temporal são sensíveis à ordem dos dados
ORDER BY data_abertura