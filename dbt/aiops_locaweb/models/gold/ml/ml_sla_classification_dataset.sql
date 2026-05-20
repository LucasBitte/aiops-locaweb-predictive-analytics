{{ config(materialized='table') }}

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

        -- ─────────────────────────────────────────────────────────────
        -- Variável alvo / Target (Y)
        -- ─────────────────────────────────────────────────────────────
        target_risco_sla

    FROM base
)

SELECT * FROM matriz_risco