{{ config(materialized='table') }}

-- ─────────────────────────────────────────────────────────────
-- dim_tempo.sql
--
-- Essa dimensão é o calendário da minha análise temporal.
-- Aqui eu expando a data de abertura em múltiplos atributos
-- para que o Power BI possa agregar incidentes por dia,
-- semana, mês, trimestre e ano sem precisar de DAX complexo.
--
-- A granularidade é diária — uma linha por dia único
-- que aparece nos dados de abertura de incidentes.
-- ─────────────────────────────────────────────────────────────

SELECT DISTINCT

    -- Surrogate key baseada na data de abertura.
    -- Converto para text antes do MD5 porque o MD5
    -- opera sobre string — sem o cast geraria erro de tipo
    MD5(COALESCE("Data_Abertura"::text, ''))            AS dim_tempo_sk,

    -- Data pura sem componente de hora —
    -- minha âncora para todos os agrupamentos temporais
    "Data_Abertura"::date                               AS data_abertura,

    -- Componentes de calendário que o Power BI e o Prophet
    -- vão usar para identificar padrões de sazonalidade

    -- Ano para análise de tendência de longo prazo
    EXTRACT(YEAR    FROM "Data_Abertura")::int          AS ano,

    -- Mês para identificar sazonalidade mensal —
    -- alguns meses têm mais incidentes por ciclos de negócio
    EXTRACT(MONTH   FROM "Data_Abertura")::int          AS mes_num,

    -- Nome do mês para exibição no Power BI sem precisar de DAX
    TO_CHAR("Data_Abertura"::date, 'Month')             AS nome_mes,

    -- Semana do ano para o Prophet capturar padrões semanais.
    -- Minha análise mostrou pico nas quintas e vale nos fins de semana
    EXTRACT(WEEK    FROM "Data_Abertura")::int          AS semana_ano,

    -- Trimestre para análise de ciclos trimestrais de negócio
    EXTRACT(QUARTER FROM "Data_Abertura")::int          AS trimestre,

    -- Ano-mês concatenado para facilitar agrupamento mensal
    -- no Power BI sem precisar de hierarquia de data
    TO_CHAR("Data_Abertura"::date, 'YYYY-MM')           AS ano_mes,

    -- Número do dia da semana: 0 = Domingo, 6 = Sábado.
    -- Uso o número no modelo preditivo e o nome no Power BI
    EXTRACT(DOW FROM "Data_Abertura")::int              AS dia_semana_num,

    -- Nome do dia para exibição nos gráficos do dashboard
    CASE EXTRACT(DOW FROM "Data_Abertura")
        WHEN 0 THEN 'Domingo'
        WHEN 1 THEN 'Segunda'
        WHEN 2 THEN 'Terca'
        WHEN 3 THEN 'Quarta'
        WHEN 4 THEN 'Quinta'
        WHEN 5 THEN 'Sexta'
        WHEN 6 THEN 'Sabado'
    END                                                 AS nome_dia,

    -- Flag de fim de semana — minha análise mostrou que
    -- nesses dias o volume cai mas a criticidade sobe
    -- porque a equipe está reduzida
    CASE
        WHEN EXTRACT(DOW FROM "Data_Abertura") IN (0,6) THEN 1
        ELSE 0
    END                                                 AS is_fim_de_semana

FROM {{ ref('stg_incidents') }}
WHERE "Data_Abertura" IS NOT NULL