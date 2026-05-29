# AIOps — Inteligência Preditiva de Incidentes
**FIAP Challenge 2026 · Locaweb · Turma 2TSCOA**

> Solução de AIOps para antecipação de incidentes operacionais, previsão de risco de OLA e apoio à decisão com recomendações práticas para a operação.

---

## Sobre o Projeto

A Locaweb registra mais de **122 mil incidentes por ano** em sua plataforma de ITSM. Sem visibilidade antecipada, o dimensionamento de equipes é reativo e o risco de violação de SLA é alto.

Este projeto transforma dados históricos de incidentes em inteligência operacional com quatro objetivos:

- **Antecipar incidentes** — prever volume para D+1 e D+7, identificando picos operacionais antes que ocorram
- **Identificar tendências** — analisar padrões por prioridade (P2 e P3 obrigatórias), categoria, produto e item de configuração
- **Projetar impacto nos KPIs** — modelar risco de perda de OLA e pressão operacional futura
- **Apoiar a decisão operacional** — responder onde agir preventivamente, quais categorias exigem atenção e quais equipes podem ser sobrecarregadas

---

## Stack Tecnológica

| Tecnologia | Papel na Solução |
|---|---|
| **AWS S3** | Data Lake com 3 camadas (Bronze: raw XLSX convertido em CSV; Silver: dados filtrados por KPI; Gold: features ML e Star Schema) |
| **RDS PostgreSQL** | Data Warehouse que centraliza dados limpidos, transforma via dbt e alimenta modelos, BI e aplicação web |
| **Terraform** | Infrastructure as Code para provisionar S3, RDS, IAM e Glue com versionamento no Git e auditoria de mudanças |
| **Apache Glue** | ETL que converte Bronze (CSV) para Silver (Parquet no S3 e staging no RDS), automatizando a ingestão com tratamento de erros |
| **dbt** | Transformação de dados versionada em SQL que aplica regras de negócio, cria Star Schema e marts ML com testes automáticos (`dbt test`) |
| **Python + scikit-learn** | Engenharia de features pós-split temporal, normalização, encoding, tratamento de outliers e validação de dados antes do treinamento |
| **Prophet** | Algoritmo de forecasting que prevê volume de incidentes para D+1 e D+7 com intervalos de confiança e detecção de sazonalidade |
| **XGBoost** | Classificador de risco que prediz probabilidade de violação de OLA por incidente com SHAP para explicabilidade |
| **K-Means** | Segmentador que agrupa incidentes em 4 clusters operacionais (A: críticos prolongados, B: recorrentes rápidos, C: sazonais, D: baixo impacto) |
| **SHAP** | Biblioteca de explicabilidade que fornece importância de features e valores SHAP para modelos XGBoost e K-Means |
| **MLflow + Azure ML** | Rastreamento centralizado de experimentos, registro de métricas (MAPE, AUC-ROC, Silhouette), artefatos e versionamento de modelos |
| **Apache Airflow** | Orquestração de DAG diária (05h UTC) que executa Glue → dbt → modelos ML → quality checks com notificação de falhas |
| **Git + GitHub** | Versionamento de código (dbt SQL, notebooks, DAGs, Terraform) com CI/CD automático (dbt test, lint, terraform plan) a cada push |
| **Power BI + Microsoft Fabric** | 5 dashboards executivos (Histórico, KPIs, Clusters, Explicabilidade, Performance) conectados ao RDS com publicação web integrada |
| **FastAPI + React** | API que expõe previsões e alertas operacionais com autenticação, integração com IA generativa (briefing diário, sentinela OLA) |
| **Docker Swarm** | Orquestração de containers que deploya FastAPI + React em `subapp.looplyai.com.br` com auto-scaling e resiliência |

---

## Arquitetura: Separação de Responsabilidades

```
┌─────────────────────────────────────────────────────────────────┐
│                          GITHUB                                 │
│                                                                 │
│  ┌─────────────────┐  ┌──────────────┐  ┌───────────────────┐   │
│  │  Repositório    │  │   Branches   │  │  CI/CD (Actions)  │   │
│  │─────────────────│  │──────────────│  │───────────────────│   │
│  │ notebooks/      │  │ main         │  │ dbt test on PR    │   │
│  │ pipeline/       │  │ develop      │  │ lint Python       │   │
│  │ dbt/            │  │ feature/e*   │  │ terraform plan    │   │
│  │ airflow/dags/   │  └──────────────┘  └───────────────────┘   │
│  │ infra/terraform │                                            │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                            AWS                                  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                        VPC                               │   │
│  │                                                          │   │
│  │  ┌─────────────────┐      ┌──────────────────────────┐   │   │
│  │  │   S3 Data Lake  │      │     RDS PostgreSQL       │   │   │
│  │  │─────────────────│      │──────────────────────────│   │   │
│  │  │ bronze/         │      │ raw_incidents_silver     │   │   │
│  │  │ silver/         │      │ star schema (gold_bi)    │   │   │
│  │  │ gold/ml/        │      │ fct_previsoes            │   │   │
│  │  │ gold/bi/        │      │ fct_ola_risk             │   │   │
│  │  │ mlflow/         │      │ fct_cluster_id           │   │   │
│  │  └────────┬────────┘      │ fct_model_metrics        │   │   │
│  │           │               └──────────────────────────┘   │   │
│  │  ┌────────▼────────┐                                     │   │
│  │  │  Apache Glue    │                                     │   │
│  │  │─────────────────│                                     │   │
│  │  │ Bronze → Silver │                                     │   │
│  │  │ S3 → RDS staging│                                     │   │
│  │  └─────────────────┘                                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                       IAM · Terraform                           │
└─────────────────────────────────────────────────────────────────┘
                │                            │
                ▼                            ▼
┌───────────────────────────┐  ┌─────────────────────────────────┐
│          AZURE            │  │               VPS               │
│                           │  │                                 │
│  ┌─────────────────────┐  │  │  ┌───────────────────────────┐  │
│  │  Azure ML Studio    │  │  │  │      Apache Airflow       │  │
│  │─────────────────────│  │  │  │───────────────────────────│  │
│  │ MLflow tracking     │  │  │  │ DAG diária 05h UTC        │  │
│  │ Model registry      │  │  │  │ Glue → dbt → ML           │  │
│  │ Experimentos        │  │  │  │ → Glue → dbt Gold BI      │  │
│  │ Prophet runs        │  │  │  │ Quality checks            │  │
│  │ XGBoost runs        │  │  │  └───────────────────────────┘  │
│  │ K-Means runs        │  │  │                                 │
│  └─────────────────────┘  │  │  ┌───────────────────────────┐  │
│                           │  │  │        dbt CLI            │  │
│  ┌─────────────────────┐  │  │  │───────────────────────────│  │
│  │   Power BI Fabric   │  │  │  │ stg_incidents             │  │
│  │─────────────────────│  │  │  │ ml_base_features          │  │
│  │ 5 dashboards        │  │  │  │ 3 marts ML                │  │
│  │ Histórico           │  │  │  │ Star Schema               │  │
│  │ KPI + Projeção      │  │  │  │ fct_model_metrics         │  │
│  │ Clusters            │  │  │  └───────────────────────────┘  │
│  │ Explicabilidade     │  │  │                                 │
│  │ Performance Modelos │  │  │  ┌───────────────────────────┐  │
│  │ Publish to Web      │  │  │  │    FastAPI + React        │  │
│  └─────────────────────┘  │  │  │───────────────────────────│  │
└───────────────────────────┘  │  │ subapp.looplyai.com.br    │  │
                               │  │ Docker Swarm              │  │
                               │  └───────────────────────────┘  │
                               └─────────────────────────────────┘
```

**Fluxo de dados:**
```
Git push → GitHub → CI (dbt test + lint + terraform plan)

S3 Bronze
    → Glue → S3 Silver → RDS (raw_incidents_silver)
        → dbt (Star Schema + marts ML) → RDS (gold_bi)
            → Python notebooks → Azure ML (treino)
                → S3 (outputs + métricas) → Glue → RDS staging
                    → dbt Gold BI (fct_previsoes + fct_model_metrics)
                        → Power BI Fabric · FastAPI · App Web
```

**Proteção contra Data Leakage em 3 camadas:**
1. **dbt** — remove colunas com informação do futuro (Status final, KPI_Violado, duração)
2. **Python** — split temporal antes de qualquer transformação matemática
3. **Python** — MinMaxScaler e encoding aplicados somente após o split

---

## 📋 Épicos do Projeto

| # | Épico | Status | MVP |
|---|---|---|---|
| E1 | **Ambiente Local** | ✅ | — |
| E2 | **Repositório** | ✅ | — |
| E3 | **Infraestrutura AWS** | ✅ | — |
| E4 | **Bronze** | ✅ | — |
| E5 | **EDA + Silver (Glue)** | 🔄 | Eng. Dados  |
| E6 | **Gold ML (Python + Azure ML)** | ⏳ | Machine Learning |
| E7 | **dbt Gold BI** | ⏳ | Eng. Dados Final |
| E8 | **Power BI** | ⏳ | Business Intelligence |
| E9 | **App Web** | ⏳ | Portal Executivo |
| E10 | **Airflow** | ⏳ | Automação e Qualidade |
| E11 | **Segurança e Observabilidade** | ⏳ | Solução Final |
| 🔁 | **Revisão e Melhorias** | ⏳ | Entrega Final |

---

## Detalhamento dos Épicos

**E5 — EDA + Silver (Glue)**
Job Glue transforma Bronze → Silver S3 (41.4k registros) e carrega no RDS. Notebook EDA valida distribuição, nulos e justificativa dos filtros KPI.

**E6 — dbt Silver + Star Schema**
`stg_incidents` lê `raw_incidents_silver`. `ml_base_features` aplica `Exige_Intervencao` e centraliza enriquecimentos. Três marts ML gerados (`ml_forecast_dataset`, `ml_sla_classification_dataset`, `ml_cluster_dataset`). Star Schema histórico completo com 6 dimensões e `fct_incidents`. Power BI já pode conectar com dados históricos ao final deste épico.

**E7 — Gold ML (Python + Azure ML)**
Notebooks leem os marts do RDS, aplicam transformações matemáticas pós-split e treinam no Azure ML. Prophet registra MAPE e RMSE. XGBoost registra AUC-ROC e PR-AUC com SHAP. K-Means registra Silhouette Score. Outputs e métricas salvos no S3.

**E8 — dbt Gold BI**
Glue carrega outputs do S3 para RDS staging. dbt cria `fct_previsoes`, `fct_ola_risk`, `fct_cluster_id`, `dim_cluster`, `fct_model_metrics` e `dim_modelo` integrando com dimensões existentes. `dbt test` valida integridade referencial antes de liberar para consumo.

**E9 — Power BI**
5 páginas conectadas ao RDS: Histórico e Tendências, KPI e Projeção de Metas, Clusters e Padrões, Explicabilidade SHAP, e Performance dos Modelos. Publicação via Microsoft Fabric.

**E10 — App Web**
Painel executivo via FastAPI + React com alertas operacionais e agentes IA (Briefing diário, Sentinela OLA, Explicador SHAP). Deploy via Docker Swarm em `subapp.looplyai.com.br`.

**E11 — Airflow**
DAG diária às 05h UTC: Glue Silver → dbt Silver/Star Schema → Notebooks ML Azure ML → Glue outputs → dbt Gold BI → quality checks em cada camada → notificação em caso de falha.

**E12 — Segurança e Observabilidade**
Contratos de dados com Pydantic, monitoramento de drift usando `fct_model_metrics`, re-treino automático por threshold, logs centralizados e rastreabilidade completa de cada previsão até o run do Azure ML.

**🔁 Revisão e Melhorias**
Ajuste de hiperparâmetros com base em `fct_model_metrics`, refinamento de dashboards e App Web, validação da DAG ponta a ponta, preparação do pitch e vídeo demonstração.

---

## Star Schema

```
dim_tempo ──────────────────────────────┐
dim_abertura ───────────────────────────┤
dim_prioridade ─────────────────────────┤──► fct_incidents      (histórico)
dim_grupo ──────────────────────────────┤
dim_produto_categoria ──────────────────┤
dim_status ─────────────────────────────┘

dim_tempo + dim_prioridade ─────────────► fct_previsoes     (Prophet)
dim_tempo + dim_grupo + dim_prioridade ─► fct_ola_risk      (XGBoost)
dim_cluster + dim_grupo ────────────────► fct_cluster_id    (K-Means)
dim_modelo ─────────────────────────────► fct_model_metrics (Azure ML)
```

---

## Modelos Preditivos

| Modelo | Algoritmo | Target | Métrica | Output RDS |
|---|---|---|---|---|
| Forecast D+1/D+7 | Prophet | Volume diário | MAPE < 20% | `fct_previsoes` |
| Risco de OLA | XGBoost + SHAP | KPI violado (0/1) | AUC-ROC > 0.85 | `fct_ola_risk` |
| Padrões operacionais | K-Means (k=4) | Cluster A/B/C/D | Silhouette > 0.5 | `fct_cluster_id` |

**4 clusters esperados:**

| Cluster | Perfil | Características |
|---|---|---|
| **A** | Críticos prolongados | Infraestrutura, P2, segunda-feira, duração > 24h |
| **B** | Recorrentes rápidos | BD/App, P3, diário, duração 1–4h |
| **C** | Sazonais previsíveis | Qualquer prioridade, início/fim de mês |
| **D** | Baixo impacto | Storage, P3, fim de semana, duração < 1h |

---

## Estrutura de Notebooks

```
notebooks/
├── 01_pre_processamento_bronze.ipynb          [E4] Conversão XLSX→CSV, upload S3
├── 02_exploratory_data_analysis_silver.ipynb  [E5] EDA, validação 41.4k registros
├── 03_dbt_transform_silver_to_gold_marts.ipynb [E6] Executa dbt, documenta SQL
├── 04_feature_engineering_ml_training.ipynb   [E7] Split + transformações pós-split
├── 05_model_forecast_prophet.ipynb            [E7] Prophet D+1/D+7 → Azure ML
├── 06_model_risk_xgboost_shap.ipynb           [E7] XGBoost + SHAP → Azure ML
└── 07_model_clustering_kmeans.ipynb           [E7] K-Means 4 clusters → Azure ML
```

---

## Estrutura de Pastas

```
aiops-locaweb/
├── infra/terraform/          # S3, RDS, IAM, Glue
├── notebooks/                # 7 notebooks por épico
├── pipeline/
│   ├── setup/                # Estrutura S3
│   ├── bronze/               # Upload XLSX
│   └── silver/               # Job Glue
├── dbt/aiops_locaweb/
│   └── models/
│       ├── staging/          # stg_incidents
│       ├── silver/           # ml_base_features + 3 marts ML
│       └── gold/
│           ├── bi/           # Star Schema + fct_model_metrics
│           └── ml/           # Features limpas para modelos
├── airflow/dags/             # Pipeline diário
├── docs/
└── requirements.txt
```

---

## Decisões Arquiteturais

**Azure ML em vez de AWS SageMaker**
MLflow tracking nativo e gratuito, sem custo de EC2, ecossistema Microsoft unificado com Power BI e Fabric, dados no S3 sem vendor lock-in, modelos em formato aberto (joblib).

**dbt para regras de negócio**
SQL versionado no Git, auditável, `dbt test` garante integridade, mesma lógica reutilizada para BI e ML sem duplicação.

**Python para matemática**
MinMaxScaler aplicado após split, reprodutível com `sklearn.joblib` e `random_state` em todos os modelos.

**Star Schema em duas fases**
Fase 1 após dbt Silver — dados históricos disponíveis para Power BI imediatamente. Fase 2 após dbt Gold BI — outputs dos modelos e métricas integrados às dimensões existentes sem recriar o schema.

**Git + GitHub**
Todo o código versionado: dbt SQL, notebooks, DAGs, Terraform. Branches por épico com merge via PR. CI/CD com dbt test, lint e terraform plan a cada push.

---

## Critérios de Avaliação (Banca Locaweb)

| Critério | Como atendemos |
|---|---|
| Clareza do problema | README com arquitetura e decisões justificadas |
| Qualidade da EDA | Notebook 02 com análise + validação das regras KPI |
| Separação dbt/Python | dbt: regras SQL testáveis · Python: matemática reproduzível |
| Proteção Data Leakage | 3 camadas: features, split, transformações matemáticas |
| Antecipação D+1/D+7 | Prophet com intervalo de confiança rastreado no Azure ML |
| Explicabilidade | SHAP values XGBoost + perfis descritivos K-Means |
| Geração de valor | 4 clusters acionáveis, alertas SLA, forecast diário |
| Reprodutibilidade | Git + dbt SQL + Python random_state + MLflow artifacts |
| Storytelling executivo | Power BI Fabric 5 páginas incluindo performance dos modelos |

---

*FIAP Challenge 2026 · Locaweb · AIOps*
*Arquitetura: dbt (regras de negócio) + Python (operações matemáticas) = proteção contra data leakage*