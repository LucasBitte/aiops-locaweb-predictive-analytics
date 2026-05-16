{{ config(materialized='table') }}

/*
    Essa é minha camada intermediária — o coração da minha arquitetura de features.
    
    Aqui eu aplico o filtro principal (Exige_Intervencao = True) uma única vez
    e calculo todos os enriquecimentos que meus três modelos vão precisar.
*/

WITH base AS (
    SELECT 
        -- Mapeamento preventivo de maiúsculas para o padrão limpo do seu script
        "Número"                AS incident_id,
        "Incidente_Pai"         AS incidente_pai,
        "Aberto_por"            AS aberto_por,
        "Prioridade"            AS prioridade,
        "Prioridade_Num"        AS prioridade_num,
        "Produto"               AS produto,
        "Categoria"             AS categoria,
        "Subcategoria"          AS subcategoria,
        "Grupo_designado"       AS grupo_designado,
        "Item_de_configuração"  AS item_configuracao,
        "Status"                AS status,
        "Código_de_fechamento" AS codigo_fechamento,
        "Entrou_para_KPI?"      AS entrou_kpi,
        "KPI_Violado?"          AS kpi_violado,
        "KPI_Status_Int"        AS kpi_status_int,
        "Possui_Pai"            AS possui_pai,
        "Exige_Intervencao"     AS exige_intervencao,
        "Target_Risco_SLA"      AS target_risco_sla,
        "Duracao_Horas"         AS duracao_horas,
        "Duração"               AS duracao_segundos,
        "Aberto"::timestamp     AS aberto_at,
        "Resolvido"::timestamp  AS resolvido_at,
        "Encerrado"::timestamp  AS encerrado_at,
        "Data_Abertura"         AS data_abertura
    FROM {{ ref('stg_incidents') }}

    -- Filtro mestre: removo ruídos de monitoramento automático.
    WHERE "Exige_Intervencao" = TRUE
),

enriquecido AS (
    SELECT
        -- ─────────────────────────────────────────────
        -- Identificadores
        -- ─────────────────────────────────────────────
        incident_id,
        incidente_pai,
        aberto_por,

        -- ─────────────────────────────────────────────
        -- Atributos originais preservados
        -- ─────────────────────────────────────────────
        prioridade,
        prioridade_num,
        produto,
        categoria,
        subcategoria,
        grupo_designado,
        item_configuracao,
        status,
        codigo_fechamento,
        entrou_kpi,
        kpi_violado,
        kpi_status_int,
        possui_pai,
        exige_intervencao,
        target_risco_sla,
        duracao_horas,
        duracao_segundos,

        -- ─────────────────────────────────────────────
        -- Timestamps originais
        -- ─────────────────────────────────────────────
        aberto_at,
        resolvido_at,
        encerrado_at,
        data_abertura,

        -- ─────────────────────────────────────────────
        -- Enriquecimentos temporais
        -- ─────────────────────────────────────────────
        EXTRACT(HOUR    FROM aberto_at)::int    AS hora_abertura,
        EXTRACT(DOW     FROM aberto_at)::int    AS dia_semana_num,
        EXTRACT(WEEK    FROM aberto_at)::int    AS semana_ano,
        EXTRACT(MONTH   FROM aberto_at)::int    AS mes_abertura,
        EXTRACT(QUARTER FROM aberto_at)::int    AS trimestre,
        TO_CHAR(aberto_at, 'YYYY-MM')           AS ano_mes,

        CASE
            WHEN EXTRACT(HOUR FROM aberto_at) BETWEEN 6  AND 11 THEN 'Manha'
            WHEN EXTRACT(HOUR FROM aberto_at) BETWEEN 12 AND 17 THEN 'Tarde'
            WHEN EXTRACT(HOUR FROM aberto_at) BETWEEN 18 AND 23 THEN 'Noite'
            ELSE 'Madrugada'
        END                                     AS turno_abertura,

        CASE
            WHEN EXTRACT(HOUR FROM aberto_at) NOT BETWEEN 8 AND 18 THEN 1
            ELSE 0
        END                                     AS fora_horario_comercial,

        CASE
            WHEN EXTRACT(DOW FROM aberto_at) IN (0,6) THEN 1
            ELSE 0
        END                                     AS abriu_fim_de_semana,

        -- ─────────────────────────────────────────────
        -- Enriquecimentos de desfecho
        -- ─────────────────────────────────────────────
        EXTRACT(EPOCH FROM (resolvido_at - aberto_at)) / 3600 AS horas_ate_resolucao,

        CASE WHEN resolvido_at IS NOT NULL THEN 1 ELSE 0 END AS foi_resolvido,

        -- ─────────────────────────────────────────────
        -- Flags de qualidade operacional
        -- ─────────────────────────────────────────────
        CASE WHEN possui_pai = 1 THEN 1 ELSE 0 END AS is_filho_de_problema,

        CASE WHEN subcategoria = 'Não Informada' THEN 1 ELSE 0 END AS triagem_incompleta,

        CASE
            WHEN codigo_fechamento IN ('Resolvido pelo Usuário', 'Sem Descrição') THEN 1
            ELSE 0
        END                                     AS fechado_sem_tecnico,

        CASE
            WHEN prioridade_num = 1 AND duracao_horas > 4  THEN 1
            WHEN prioridade_num = 2 AND duracao_horas > 8  THEN 1
            WHEN prioridade_num = 3 AND duracao_horas > 24 THEN 1
            WHEN prioridade_num = 4 AND duracao_horas > 72 THEN 1
            ELSE 0
        END                                     AS excedeu_tempo_esperado,

        -- ─────────────────────────────────────────────
        -- Score de risco operacional composto
        -- ─────────────────────────────────────────────
        (
            CASE WHEN target_risco_sla = 1     THEN 3 ELSE 0 END +
            CASE WHEN prioridade_num   <= 2    THEN 2 ELSE 0 END +
            CASE WHEN exige_intervencao = TRUE THEN 1 ELSE 0 END +
            CASE WHEN possui_pai = 1           THEN 1 ELSE 0 END +
            CASE WHEN EXTRACT(HOUR FROM aberto_at) NOT BETWEEN 8 AND 18 THEN 1 ELSE 0 END
        )                                       AS score_risco_operacional

    FROM base
)

SELECT * FROM enriquecido