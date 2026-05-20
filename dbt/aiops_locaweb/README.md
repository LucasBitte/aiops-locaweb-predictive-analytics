# dbt - AIOps Locaweb

Projeto dbt para transformações de dados da Locaweb ITSM.

## Estrutura de Modelos

```
models/
├── staging/
│   ├── sources.yml          # Definição da fonte (raw_incidents_silver do RDS)
│   └── stg_incidents.sql    # View com limpeza base
│
├── silver/
│   ├── schema.yml
│   └── ml_base_features.sql # Table com features de ML
│
└── gold/
    ├── bi/
    │   ├── schema.yml
    │   ├── dim_abertura.sql
    │   ├── dim_grupo.sql
    │   ├── dim_prioridade.sql
    │   ├── dim_produto_categoria.sql
    │   ├── dim_status.sql
    │   ├── dim_tempo.sql
    │   ├── fct_incidents.sql          # Star Schema - Fact Table
    │   └── fct_model_metrics.sql      # Métricas de modelos ML (daily)
    │
    └── ml/
        ├── schema.yml
        ├── ml_base_features.sql       # Features limpas
        ├── ml_cluster_dataset.sql     # Dataset para K-Means
        ├── ml_forecast_dataset.sql    # Dataset para Prophet D+1/D+7
        └── ml_sla_classification_dataset.sql  # Dataset para XGBoost
```

## Schemas RDS

| Schema | Finalidade | Materialização |
|--------|-----------|---|
| `public` | Staging (sources) | VIEW |
| `silver` | Features refinadas | TABLE |
| `gold` | Star Schema + ML datasets | TABLE |

## Fluxo de Dados

```
RDS (raw_incidents_silver)
    ↓
[staging] stg_incidents (VIEW)
    ↓
[silver] ml_base_features (TABLE)
    ↓ ├→ [gold/bi] Star Schema (dims + fct_incidents)
    ↓ ├→ [gold/bi] fct_model_metrics (tracking)
    ↓ └→ [gold/ml] Datasets ML (3 modelos)
    ↓
Power BI + MLflow/Azure ML
```

## Instalação e Setup

### 1. Configurar variáveis de ambiente

```bash
$env:RDS_HOST = "seu-endpoint.rds.amazonaws.com"
$env:RDS_USER = "admin"
$env:RDS_PASSWORD = "senha"
$env:RDS_DATABASE = "aiops"
```

### 2. Instalar dependências dbt

```bash
pip install dbt-postgres
```

### 3. Testar conexão

```bash
dbt debug
```

### 4. Executar transformações

```bash
# Rodar staging
dbt run --select staging

# Rodar silver
dbt run --select silver

# Rodar gold
dbt run --select gold

# Rodar tudo
dbt run

# Testes
dbt test
```

## Modelos Principais

### Staging
- **stg_incidents**: View raw com limpeza base do source ITSM

### Silver
- **ml_base_features**: Features de engenharia (Data_Abertura, Ano_Mes, Prioridade_Num, etc)

### Gold - BI
- **dim_abertura**: Contexto intradiário (timestamp exato)
- **dim_grupo**: Equipes designadas
- **dim_prioridade**: Níveis de prioridade (1-5) com SLA thresholds
- **dim_produto_categoria**: Produtos e categorias
- **dim_status**: Status e códigos de fechamento
- **dim_tempo**: Calendário analítico (data_abertura)
- **fct_incidents**: Fact table central (Star Schema)
- **fct_model_metrics**: Rastreamento diário de desempenho dos modelos

### Gold - ML
- **ml_cluster_dataset**: Features normalizadas para K-Means
- **ml_forecast_dataset**: Features com lags/rolling para Prophet
- **ml_sla_classification_dataset**: Features para XGBoost OLA Risk

## Documentação

Gerar docs:
```bash
dbt docs generate
dbt docs serve
```

## Status

- ✅ Staging: sources + stg_incidents
- ✅ Silver: ml_base_features
- ✅ Gold/BI: Star Schema (6 dims + 1 fct + 1 metrics)
- ✅ Gold/ML: 3 datasets ML
- ⏳ Testes (unique, not_null, relationships)
