{{ config(
    materialized='table',
    schema='gold_bi',
    tags=['dimension', 'bi']
) }}

-- ─────────────────────────────────────────────────────────────
-- dim_status.sql
--
-- Essa dimensão descreve o estado final de encerramento
-- do chamado e sua elegibilidade para as metas de KPI.
--
-- Concateno status e código de fechamento na chave porque
-- um mesmo status pode ter múltiplos códigos de fechamento —
-- por exemplo, "Encerrado" pode ser "Resolvido pelo Usuário"
-- ou "Sucesso", que têm significados operacionais distintos
-- ─────────────────────────────────────────────────────────────

SELECT DISTINCT

    -- Surrogate key composta por status e código de fechamento com delimitador.
    -- Preciso dos dois para garantir que cada combinação
    -- de desfecho tenha sua própria linha na dimensão
    MD5(
        COALESCE("Status", 'sem_status') || '||' ||
        COALESCE("Codigo_de_fechamento", 'sem_codigo')
    )                                                 AS dim_status_sk,

    -- Estado final do chamado no momento da extração.
    -- Indica em que fase do ciclo de vida o ticket estava
    COALESCE("Status", 'Não Informado')               AS status,

    -- Categoria do desfecho — como o chamado foi encerrado.
    -- Nulos foram tratados na silver como 'Não Encerrado'
    -- para representar chamados que ainda estavam ativos
    COALESCE("Codigo_de_fechamento", 'Não Informado') AS codigo_fechamento,

    -- Flag contratual: esse chamado entrava nas metas de SLA?
    -- Alguns tipos de chamado são isentos por regra comercial —
    -- incluo aqui para filtrar corretamente nas análises de KPI
    "Entrou_para_KPI"                                AS entrou_kpi

FROM {{ ref('stg_incidents') }}
WHERE "Status" IS NOT NULL