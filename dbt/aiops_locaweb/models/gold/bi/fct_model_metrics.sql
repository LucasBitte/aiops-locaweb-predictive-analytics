-- Tabela fato de métricas dos modelos ML
-- Rastreia desempenho diário dos modelos (Forecast D+1/D+7, OLA Risk, Clustering)
-- Alimenta dashboards de monitoramento em tempo real no Power BI

{{ config(
    materialized='table',
    schema='gold_bi',
    tags=['model_metrics', 'daily']
) }}

with model_metrics as (
    select
        current_date as data_metrica,
        'forecast_d1' as modelo_tipo,
        null::float as mape,
        null::float as rmse,
        null::float as auc_roc,
        null::int as amostras,
        null::text as status

    union all

    select
        current_date,
        'forecast_d7',
        null, null, null, null, null

    union all

    select
        current_date,
        'ola_risk',
        null, null, null, null, null

    union all

    select
        current_date,
        'clustering',
        null, null, null, null, null
)

select * from model_metrics
