{{ config(materialized='table') }}

-- ─────────────────────────────────────────────────────────────
-- dim_grupo.sql
--
-- Essa dimensão representa as equipes responsáveis pelo
-- atendimento dos incidentes.
-- É uma das features de maior impacto no risco de SLA —
-- a análise exploratória mostrou que o grupo designado
-- é um dos principais preditores de violação.
-- ─────────────────────────────────────────────────────────────

SELECT DISTINCT

    -- Surrogate key gerada a partir do nome do grupo.
    -- Como o nome é único por equipe, o MD5 de um campo
    -- já é suficiente para garantir unicidade aqui
    MD5(COALESCE("Grupo_designado", ''))                AS dim_grupo_sk,

    -- Nome da equipe responsável pelo atendimento.
    -- No Power BI uso essa coluna para filtrar métricas
    -- por equipe e identificar quais estão sobrecarregadas
    "Grupo_designado"                                   AS grupo_designado

FROM {{ ref('stg_incidents') }}
WHERE "Grupo_designado" IS NOT NULL