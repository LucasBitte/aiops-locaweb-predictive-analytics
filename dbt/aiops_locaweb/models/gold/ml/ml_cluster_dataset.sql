{{ config(materialized='table') }}

/*
    Esse mart alimenta meu modelo de Clusterização (Modelo 06).
    
    Aqui a lógica é completamente diferente do mart_matriz_risco.
    Na clusterização não estou prevendo o futuro — estou descrevendo
    o passado completo para encontrar grupos de comportamento similar.
*/

WITH base AS (
    SELECT * FROM {{ ref('ml_base_features') }}
    -- Consumindo a Feature Store mestre que já possui o filtro Exige_Intervencao = TRUE
),

perfis AS (
    SELECT
        -- Mantenho o ID para rastreabilidade no Python
        incident_id,

        -- ─────────────────────────────────────────────
        -- Dimensão de CAUSA — o contexto de abertura
        -- ─────────────────────────────────────────────
        prioridade_num,
        grupo_designado,
        categoria,
        subcategoria,
        produto,
        hora_abertura,
        turno_abertura,
        dia_semana_num,
        fora_horario_comercial,
        abriu_fim_de_semana,
        mes_abertura,
        trimestre,
        possui_pai,
        is_filho_de_problema,
        triagem_incompleta,

        -- ─────────────────────────────────────────────
        -- Dimensão de EFEITO — o desfecho operacional
        -- ─────────────────────────────────────────────
        duracao_horas,
        horas_ate_resolucao,
        foi_resolvido,
        excedeu_tempo_esperado,
        fechado_sem_tecnico,
        target_risco_sla,
        kpi_status_int,
        score_risco_operacional,

        -- ─────────────────────────────────────────────
        -- Placeholders para transformações no Python
        -- ─────────────────────────────────────────────
        NULL::float AS duracao_horas_scaled,   -- preenchido pelo Python
        NULL::int   AS cluster_id              -- preenchido pelo Python após treino

    FROM base
)

SELECT * FROM perfis