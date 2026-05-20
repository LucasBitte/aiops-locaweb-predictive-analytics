{{ config(
    materialized='table',
    schema='gold_bi',
    tags=['fact', 'bi', 'star_schema']
) }}

/*
    Essa é minha tabela fato central do star schema.
    
    Aqui eu concentro todas as métricas mensuráveis de cada incidente,
    mantendo a granularidade no nível de ticket individual.
    
    As descrições e atributos textuais ficam nas dimensões —
    la fato só guarda números, chaves e flags binárias.
    Essa separação é o que permite o Power BI fazer os relacionamentos
    e agregar qualquer métrica por qualquer dimensão.
*/

SELECT
    -- ─────────────────────────────────────────────────────────────
    -- Chaves (Surrogate Keys) Alinhadas com as Dimensões
    -- ─────────────────────────────────────────────────────────────

    -- Chave única da fato — gerada a partir do número do incidente
    MD5(COALESCE("Numero", ''))                                 AS incident_sk,

    -- FK para dim_produto_categoria (Alinhada com delimitadores)
    MD5(COALESCE("Produto", '') || '||' || COALESCE("Categoria", '') || '||' || COALESCE("Subcategoria", '')) AS dim_produto_categoria_sk,

    -- FK para dim_grupo — equipe responsável pelo atendimento
    MD5(COALESCE("Grupo_designado", ''))                        AS dim_grupo_sk,

    -- FK para dim_tempo — âncora de data para análise temporal
    MD5(COALESCE("Data_Abertura"::text, ''))                    AS dim_tempo_sk,

    -- FK para dim_status — (Alinhada com delimitadores e fallbacks)
    MD5(COALESCE("Status", 'sem_status') || '||' || COALESCE("Codigo_de_fechamento", 'sem_codigo')) AS dim_status_sk,

    -- FK para dim_prioridade — separei prioridade em dimensão própria
    MD5(COALESCE("Prioridade_Num"::text, ''))                   AS dim_prioridade_sk,

    -- FK para dim_abertura — dimensão com enriquecimentos do timestamp
    MD5(COALESCE("Aberto"::text, ''))                           AS dim_abertura_sk,

    -- ─────────────────────────────────────────────────────────────
    -- Chave degenerada
    -- ─────────────────────────────────────────────────────────────
    "Numero"                                                    AS incident_id,

    -- ─────────────────────────────────────────────────────────────
    -- Métricas brutas
    -- ─────────────────────────────────────────────────────────────
    "Duracao_Horas"                                             AS duracao_horas,
    "Duracao"                                                   AS duracao_segundos,
    "KPI_Violado"                                               AS kpi_status_int,
    "Target_Risco_SLA"                                          AS target_risco_sla,
    "Exige_Intervencao"::int                                    AS exige_intervencao,
    "Possui_Pai"                                                AS possui_pai,

    -- ─────────────────────────────────────────────────────────────
    -- Métricas calculadas
    -- ─────────────────────────────────────────────────────────────
    EXTRACT(EPOCH FROM (
        "Resolvido"::timestamp - "Aberto"::timestamp
    )) / 3600                                                   AS horas_ate_resolucao,

    CASE WHEN "Resolvido" IS NOT NULL THEN 1 ELSE 0 END         AS foi_resolvido,

    -- ─────────────────────────────────────────────────────────────
    -- Flags binárias de comportamento
    -- ─────────────────────────────────────────────────────────────
    CASE WHEN "Incidente_Pai" != 'Independente'
        THEN 1 ELSE 0 END                                       AS is_filho_de_problema,

    CASE WHEN "Subcategoria" = 'Não Informada'
        THEN 1 ELSE 0 END                                       AS triagem_incompleta,

    CASE WHEN "Codigo_de_fechamento"
        IN ('Resolvido pelo Usuário','Sem Descrição')
        THEN 1 ELSE 0 END                                       AS fechado_sem_tecnico,

    CASE
        WHEN "Prioridade_Num" = 1 AND "Duracao_Horas" > 4  THEN 1
        WHEN "Prioridade_Num" = 2 AND "Duracao_Horas" > 8  THEN 1
        WHEN "Prioridade_Num" = 3 AND "Duracao_Horas" > 24 THEN 1
        WHEN "Prioridade_Num" = 4 AND "Duracao_Horas" > 72 THEN 1
        ELSE 0
    END                                                         AS excedeu_tempo_esperado,

    -- ─────────────────────────────────────────────────────────────
    -- Score de risco operacional composto
    -- ─────────────────────────────────────────────────────────────
    (
        CASE WHEN "Target_Risco_SLA" = 1     THEN 3 ELSE 0 END +
        CASE WHEN "Prioridade_Num" <= 2      THEN 2 ELSE 0 END +
        CASE WHEN "Exige_Intervencao" = 1 THEN 1 ELSE 0 END +
        CASE WHEN "Possui_Pai" = 1           THEN 1 ELSE 0 END +
        CASE WHEN EXTRACT(HOUR FROM "Aberto"::timestamp)
             NOT BETWEEN 8 AND 18            THEN 1 ELSE 0 END
    )                                                           AS score_risco_operacional,

    -- ─────────────────────────────────────────────────────────────
    -- Timestamps originais
    -- ─────────────────────────────────────────────────────────────
    "Aberto"::timestamp                                         AS aberto_at,
    "Resolvido"::timestamp                                      AS resolvido_at,
    "Encerrado"::timestamp                                      AS encerrado_at

FROM {{ ref('stg_incidents') }}