{{ config(
    materialized='table',
    schema='gold_ml',
    tags=['ml_dataset', 'classification', 'sla_risk']
) }}

/*
    Esse mart alimenta meu classificador de risco de SLA (Modelo 05).
    
    A regra mais importante aqui é o que EU NÃO INCLUO.
    
    Estou simulando o estado de informação do sistema no exato
    momento em que o ticket é aberto — os primeiros 5 minutos de vida.
*/

WITH base AS (
    SELECT * FROM {{ ref('ml_base_features') }}
    -- Consumindo a Feature Store mestre que já possui o filtro Exige_Intervencao = TRUE
),

matriz_risco AS (
    SELECT
        -- ─────────────────────────────────────────────────────────────
        -- Identificador (Crucial para Tracking e Split no Python)
        -- ─────────────────────────────────────────────────────────────
        incident_id,

        -- ─────────────────────────────────────────────────────────────
        -- Features disponíveis no minuto 0 de abertura
        -- ─────────────────────────────────────────────────────────────
        prioridade_num,
        grupo_designado,
        categoria,
        subcategoria,
        possui_pai,
        is_filho_de_problema,
        triagem_incompleta,

        -- Features temporais de abertura
        hora_abertura,
        dia_semana_num,
        turno_abertura,
        fora_horario_comercial,
        abriu_fim_de_semana,
        semana_ano,
        mes_abertura,
        duracao_horas,

        -- ─────────────────────────────────────────────────────────────
        -- Variáveis alvo / Target (Y)
        -- ─────────────────────────────────────────────────────────────
        target_risco_sla,

        -- Target: excedeu tempo esperado por prioridade?
        -- Thresholds: P1=4h, P2=8h, P3=24h, P4=72h
        CASE
            WHEN prioridade_num = 1 AND duracao_horas > 4 THEN 1
            WHEN prioridade_num = 2 AND duracao_horas > 8 THEN 1
            WHEN prioridade_num = 3 AND duracao_horas > 24 THEN 1
            WHEN prioridade_num = 4 AND duracao_horas > 72 THEN 1
            ELSE 0
        END AS target_excedeu_tempo

    FROM base
)

SELECT * FROM matriz_risco