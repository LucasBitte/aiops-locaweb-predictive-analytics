{{ config(materialized='table') }}

-- ─────────────────────────────────────────────────────────────
-- dim_abertura.sql
--
-- Essa dimensão enriquece o timestamp de abertura com
-- atributos de contexto operacional que não cabem na dim_tempo.
--
-- A diferença entre dim_tempo e dim_abertura é a granularidade:
--   dim_tempo  → granularidade de DIA  (uma linha por data)
--   dim_abertura → granularidade de TIMESTAMP (uma linha por abertura)
--
-- Isso me permite analisar padrões intradiários como
-- horário de pico, turno com mais violações e
-- comportamento fora do horário comercial
-- ─────────────────────────────────────────────────────────────

SELECT DISTINCT

    -- Surrogate key baseada no timestamp completo de abertura.
    -- Uso o timestamp e não só a data porque precisamos
    -- de granularidade de hora para análise de turno
    MD5(COALESCE("Aberto"::text, ''))                   AS dim_abertura_sk,

    -- Timestamp original preservado para drill-down fino
    "Aberto"::timestamp                                 AS aberto_at,

    -- Hora de abertura extraída do timestamp.
    -- Feature de alta importância no modelo de classificação —
    -- incidentes abertos de madrugada têm maior risco de SLA
    -- porque a equipe está em sobreaviso com capacidade reduzida
    EXTRACT(HOUR FROM "Aberto"::timestamp)::int         AS hora_abertura,

    -- Classificação do período do dia em turnos operacionais.
    -- Uso isso no Power BI para filtrar por turno e identificar
    -- qual período concentra mais incidentes críticos
    CASE
        WHEN EXTRACT(HOUR FROM "Aberto"::timestamp)
             BETWEEN 6  AND 11 THEN 'Manha'
        WHEN EXTRACT(HOUR FROM "Aberto"::timestamp)
             BETWEEN 12 AND 17 THEN 'Tarde'
        WHEN EXTRACT(HOUR FROM "Aberto"::timestamp)
             BETWEEN 18 AND 23 THEN 'Noite'
        ELSE                        'Madrugada'
    END                                                 AS turno_abertura,

    -- Flag de horário fora do comercial.
    -- Minha hipótese, confirmada na análise exploratória,
    -- é que incidentes fora do horário 08h-18h têm
    -- maior probabilidade de violar SLA
    CASE
        WHEN EXTRACT(HOUR FROM "Aberto"::timestamp)
             NOT BETWEEN 8 AND 18 THEN 1
        ELSE 0
    END                                                 AS fora_horario_comercial,

    -- Flag de fim de semana no timestamp de abertura.
    -- Diferente da dim_tempo que olha para a data,
    -- aqui eu valido o dia da semana no momento exato
    -- do registro para não ter divergência de classificação
    CASE
        WHEN EXTRACT(DOW FROM "Aberto"::timestamp)
             IN (0,6) THEN 1
        ELSE 0
    END                                                 AS abriu_fim_de_semana

FROM {{ ref('stg_incidents') }}
WHERE "Aberto" IS NOT NULL