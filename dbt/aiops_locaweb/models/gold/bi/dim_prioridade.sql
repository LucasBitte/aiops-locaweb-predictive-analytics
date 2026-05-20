{{ config(
    materialized='table',
    schema='gold_bi',
    tags=['dimension', 'bi']
) }}

-- ─────────────────────────────────────────────────────────────
-- dim_prioridade.sql
--
-- Separei prioridade em uma dimensão própria porque ela
-- tem atributos descritivos e bucketing que poluiriam a fato
-- se ficassem lá.
--
-- Além disso, o challenge exige análise obrigatória de P2 e P3 —
-- tendo uma dimensão dedicada, o Power BI consegue filtrar
-- e segmentar por prioridade com um único clique,
-- sem precisar de medidas DAX para parsing de texto
-- ─────────────────────────────────────────────────────────────

SELECT DISTINCT

    -- Surrogate key baseada no número da prioridade.
    -- Converto para text porque o MD5 exige string como input
    MD5(COALESCE("Prioridade_Num"::text, ''))           AS dim_prioridade_sk,

    -- Número da prioridade — de 1 (mais crítico) a 5 (menos crítico).
    -- Uso esse campo nas fórmulas do modelo preditivo
    -- porque modelos matemáticos operam em número, não em texto
    "Prioridade_Num"::int                               AS prioridade_num,

    -- Texto descritivo original da prioridade.
    -- Mantenho para rastreabilidade e para exibição
    -- nos tooltips do Power BI
    "Prioridade"                                        AS prioridade_texto,

    -- Bucket padronizado que criei para simplificar
    -- a leitura nos dashboards — substitui o texto
    -- original que varia por sistema ITSM
    CASE "Prioridade_Num"
        WHEN 1 THEN 'P1 - Critica'
        WHEN 2 THEN 'P2 - Alta'
        WHEN 3 THEN 'P3 - Moderada'
        WHEN 4 THEN 'P4 - Baixa'
        ELSE        'Nao Classificada'
    END                                                 AS bucket_prioridade,

    -- Classificação binária de criticidade.
    -- P1 e P2 são críticos por impactarem diretamente
    -- os acordos comerciais de maior penalidade financeira
    CASE
        WHEN "Prioridade_Num" <= 2 THEN 'Critico'
        ELSE                            'Normal'
    END                                                 AS nivel_criticidade,

    -- Threshold de SLA em horas para cada prioridade.
    -- Esses valores refletem as regras contratuais da operação
    -- e são a base para o cálculo de excedeu_tempo_esperado na fato
    CASE "Prioridade_Num"
        WHEN 1 THEN 4
        WHEN 2 THEN 8
        WHEN 3 THEN 24
        WHEN 4 THEN 72
        ELSE NULL
    END                                                 AS threshold_sla_horas

FROM {{ ref('stg_incidents') }}
WHERE "Prioridade_Num" IS NOT NULL