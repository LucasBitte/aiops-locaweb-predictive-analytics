# AIOps — Inteligência Preditiva de Incidentes
**FIAP Challenge 2026 · Locaweb · Turma 2TSCOA**

> Solução de AIOps para antecipação de incidentes operacionais, previsão de risco de OLA e apoio à decisão com recomendações práticas para a operação.

---

## Sobre o Projeto

A Locaweb registra mais de **122 mil incidentes por ano** em sua plataforma de ITSM. Sem visibilidade antecipada, o dimensionamento de equipes é reativo e o risco de violação de SLA é alto.

Este projeto transforma dados históricos de incidentes em inteligência operacional, respondendo às perguntas:

- **Quantos incidentes vão abrir amanhã e na próxima semana?**
- **Qual a probabilidade de violar o OLA por incidente?**
- **Onde devo agir preventivamente hoje?**
- **Quais equipes podem ser sobrecarregadas?**

---

## Stack Tecnológica

| Camada | Tecnologia |
|---|---|
| Infraestrutura | AWS S3 · RDS PostgreSQL · Terraform |
| **Transformações (regras de negócio)** | **dbt + SQL** |
| **Transformações (operações matemáticas)** | **Python + scikit-learn** |
| Modelagem | Prophet · XGBoost · K-Means · SHAP |
| Tracking | MLflow · Azure ML Studio |
| Orquestração | Apache Airflow (VPS Coolify) |
| Serving | Power BI · Microsoft Fabric |

---

## Arquitetura: Separação de Responsabilidades

```
Bronze (ITSM Bruto - 122k registros)
    │
    ├─→ [dbt: Regras de Negócio]
    │   ├─ Filtro: Exige_Intervencao (Status != 'Sem Intervenção')
    │   ├─ Exclusão: Colunas que causam data leakage
    │   ├─ Agrupamento: Temporal (ano/mês/semana)
    │   └─ Versão: SQL rastreável e versionada
    │
    ├─→ Silver (41.4k registros elegíveis para ML)
    │   │
    │   ├─→ [dbt: Star Schema para BI]
    │   │   ├─ Dimensões: tempo, prioridade, produto, grupo, cluster
    │   │   ├─ Fatos: volume diário, violações
    │   │   └─ Armazenado: RDS PostgreSQL
    │   │
    │   └─→ [Python: Matemática ML]
    │       ├─ Split treino/teste (previne leakage)
    │       ├─ MinMaxScaler (apenas post-split)
    │       ├─ One-Hot Encoding (apenas pós-split)
    │       ├─ Treino: Prophet, XGBoost, K-Means
    │       └─ Armazenado: MLflow/Azure ML
    │
    └─→ Gold
        ├─ Gold/BI: Star Schema (Power BI) — dbt
        └─ Gold/ML: Features ML (Modelos) — Python
```

### Por que essa separação?

**dbt (regras de negócio em SQL)**:
- ✅ Rastreável via Git
- ✅ Auditável via SQL
- ✅ Reutilizável em múltiplos contextos
- ✅ Versionado e testado
- ✅ Previne leakage de **regras** (ex: não posso filtrar por "Status" após saber o resultado)

**Python (operações matemáticas)**:
- ✅ Bibliotecas científicas (scikit-learn, Prophet, XGBoost)
- ✅ Split treino/teste obrigatório
- ✅ Normalização APÓS split (previne leakage de **escala**)
- ✅ Facilita reprodutibilidade com random_state
- ✅ MLflow tracks versões de modelos

**Proteção contra Data Leakage em 2 camadas**:
1. **Layer 1 (dbt)**: Remove informações que você não teria em produção (Status final, se foi violado, etc)
2. **Layer 2 (Python)**: Aplica transformações matemáticas APÓS split treino/teste

---

## 📋 Épicos do Projeto (10 fases)

| # | Épico | Status | Descrição |
|---|---|---|---|
| E1 | **Ambiente Local** | ✅ | VS Code + Python 3.11 + Git + AWS CLI + MLflow |
| E2 | **Repositório** | ✅ | Estrutura do projeto versionada no GitHub |
| E3 | **Infraestrutura AWS** | ✅ | Terraform: S3 Data Lake + RDS PostgreSQL + IAM |
| E4 | **Bronze (Ingestão)** | ✅ | Upload XLSX → S3 (122k registros brutos) |
| E5 | **EDA + Silver (Glue)** | 🔄 | Apache Glue: Bronze→Silver com validações (41.4k registros) |
| E6 | **Silver (dbt)** | ⏳ | dbt: Regras de negócio em SQL (filtro, agrupamento, star schema) |
| E7 | **Gold (dbt + Python)** | ⏳ | dbt: features para BI + Python: features para ML com split treino/teste |
| E8 | **Modelos ML** | ⏳ | Python: Prophet + XGBoost + K-Means com MLflow tracking |
| E9 | **Airflow** | ⏳ | Orquestração: Glue→dbt→Python→Power BI (agendamento diário) |
| E10 | **Power BI** | ⏳ | 4 dashboards interativos + Microsoft Fabric sharing |

---

## Estrutura de Notebooks (Objetivo claro de cada um)

```
notebooks/
├── E4-E5: INGESTÃO E ANÁLISE EXPLORATÓRIA
│   ├── 01_pre_processamento_bronze.ipynb
│   │   └─ Objetivo: Converte XLSX→CSV, validação schema, upload S3
│   │
│   └── 02_exploratory_data_analysis_silver.ipynb
│       └─ Objetivo: EDA completa, valida regras KPI, justifica filtros
│           • Distribuição de incidentes por tipo/prioridade/data
│           • Análise de nulos e anomalias
│           • Validação: 41.4k registros elegíveis
│           • Por que filtrar por Status/Data? → regras de negócio
│
├── E6-E7: TRANSFORMAÇÃO DE DADOS (regras de negócio em SQL)
│   └── 03_dbt_transform_silver_to_gold_marts.ipynb
│       └─ Objetivo: Executa dbt models, documenta SQL
│           • Silver→Gold: filtro Exige_Intervencao (dbt)
│           • Gold/BI: dimensões e fatos para Power BI (dbt)
│           • Gold/ML: agregações temporais sem leakage (dbt)
│           • Validações dbt: unique, not_null, relationships
│
├── E7-E8: TRANSFORMAÇÃO MATEMÁTICA (Python pós-split)
│   ├── 04_feature_engineering_ml_training.ipynb
│   │   └─ Objetivo: Matemática de features APÓS treino/teste split
│   │       • MinMaxScaler (apenas post-split)
│   │       • One-Hot Encoding (apenas post-split)
│   │       • Calcula média/std do treino → aplica em teste
│   │       • Preventivo contra data leakage
│   │
│   ├── 05_model_forecast_prophet.ipynb
│   │   └─ Objetivo: Treina Prophet D+1/D+7
│   │       • Input: features de Gold/ML (limpo pelo dbt)
│   │       • Output: MLflow logs de MAPE, visualizações
│   │
│   ├── 06_model_risk_xgboost_shap.ipynb
│   │   └─ Objetivo: XGBoost + SHAP para risco de OLA
│   │       • Classificação binária: violado (1) vs OK (0)
│   │       • SHAP values: explainability dos top features
│   │       • Output: MLflow logs de AUC-ROC, feature importance
│   │
│   └── 07_model_clustering_kmeans.ipynb
│       └─ Objetivo: K-Means com 4 clusters de padrões
│           • Agrupa por horário/dia/prioridade/duração
│           • Output: MLflow logs de Silhouette Score
│           • Cluster labels para BI
│
└── E9-E10: ORQUESTRAÇÃO E SERVING
    ├── airflow/dags/aiops_pipeline_dag.py
    │   └─ Orquestra: Glue→dbt→Python→Power BI (diário)
    │
    └── Power BI / Microsoft Fabric (4 dashboards)
        └─ Consulta: RDS Gold/BI (star schema via dbt)
```

---

## Estrutura de Pastas (Versão Atual)

```
aiops-locaweb/
├── infra/terraform/              # Terraform: S3, RDS, IAM, Glue
│   ├── main.tf, variables.tf, outputs.tf
│   ├── modules/
│   │   ├── network/
│   │   ├── storage/
│   │   ├── database/
│   │   └── glue/                 # [Novo] Job Glue
│   └── README_MODULOS.md
│
├── notebooks/
│   ├── 01_pre_processamento_bronze.ipynb       [E4]
│   ├── 02_exploratory_data_analysis_silver.ipynb [E5]
│   ├── 03_dbt_transform_silver_to_gold_marts.ipynb [E6-E7]
│   ├── 04_feature_engineering_ml_training.ipynb [E7-E8]
│   ├── 05_model_forecast_prophet.ipynb         [E8]
│   ├── 06_model_risk_xgboost_shap.ipynb        [E8]
│   └── 07_model_clustering_kmeans.ipynb        [E8]
│
├── pipeline/
│   ├── setup/create_s3_structure.py            # E4
│   ├── bronze/upload_xlsx.py                   # E4
│   └── silver/                                 # E5 (Glue)
│       ├── __init__.py
│       ├── config.py
│       ├── transformations.py
│       ├── validators.py
│       ├── logger.py
│       ├── transform_bronze_to_silver.py       # Job Glue principal
│       ├── test_transformations.py
│       ├── requirements-silver.txt
│       └── README.md
│
├── dbt/aiops_locaweb/                          # E6-E7
│   ├── models/
│   │   ├── staging/stg_*.sql                   # Bronze→Silver prep
│   │   ├── silver/slv_*.sql                    # Silver: regras KPI
│   │   ├── gold/
│   │   │   ├── ml/gold_*_ml.sql                # Gold/ML: features limpas
│   │   │   └── bi/                             # Gold/BI: star schema
│   │   │       ├── dim_*.sql                   # Dimensões
│   │   │       ├── fact_incidents_kpi.sql      # Fato principal
│   │   │       └── vw_painel_geral.sql         # Views para Power BI
│   │   └── schema.yml
│   ├── tests/
│   ├── profiles.yml
│   └── dbt_project.yml
│
├── airflow/dags/                               # E9
│   └── aiops_pipeline_dag.py
│
├── docs/
│   ├── ARQUITETURA_NOTEBOOKS.md                # Mapa completo
│   ├── TERRAFORM_MODULARIZADO.md
│   └── PROJECT_CONTEXT.md
│
├── .env.example
├── CLAUDE.md                      # Setup detalhado
├── README.md                      # Este arquivo
└── requirements.txt
```

---

## 🤖 Modelos Preditivos (E8)

### 1️⃣ Forecast: Prophet (D+1 e D+7)

| Aspecto | Detalhes |
|---|---|
| **Objetivo** | Prever volume total de incidentes em D+1 e D+7 |
| **Algoritmo** | Facebook Prophet (séries temporais com sazonalidade) |
| **Input** | Gold/ML: volume agregado por dia (41.4k registros) |
| **Target** | Quantidade de incidentes (numérico) |
| **Métrica** | MAPE < 20% |
| **Output** | MLflow: MAPE, RMSE, gráficos de forecast |
| **Uso Operacional** | "Preciso escalar + pessoas na segunda? Vamos ver D+1" |

### 2️⃣ Classificação: XGBoost + SHAP (Risco de OLA)

| Aspecto | Detalhes |
|---|---|
| **Objetivo** | Identificar incidentes com risco ALTO de violar SLA |
| **Algoritmo** | XGBoost (classificação binária) + SHAP (explicabilidade) |
| **Input** | Gold/ML: features de prioridade, duração, categoria, hora |
| **Target** | 0 = OK (98.6%) / 1 = Violado (1.4%) ← imbalanced (proposital) |
| **Métrica** | AUC-ROC > 0.85 |
| **Output** | MLflow: AUC-ROC, PR-AUC, SHAP feature importance |
| **Uso Operacional** | "Este incidente P3 tem 75% de chance de violar. Alocar especialista agora." |

### 3️⃣ Clustering: K-Means (Padrões Operacionais)

| Aspecto | Detalhes |
|---|---|
| **Objetivo** | Agrupar incidentes em padrões similares |
| **Algoritmo** | K-Means com k=4 clusters |
| **Input** | Gold/ML: hora/dia/prioridade/duração/categoria |
| **Target** | N/A (unsupervised) |
| **Métrica** | Silhouette Score > 0.5 |
| **Output** | MLflow: Silhouette Score, cluster centers, labels |
| **Clusters Esperados** | |
| **A — Críticos prolongados** | Infraestrutura, P2, segunda-feira, duração > 24h, alto OLA |
| **B — Recorrentes rápidos** | BD/App, P3, diário, duração 1-4h, baixo OLA |
| **C — Sazonais previsíveis** | Qualquer prioridade, início/fim de mês, padrão claro |
| **D — Baixo impacto** | Storage, P3/P4, fim de semana, duração < 1h |

### Proteção contra Data Leakage em Cada Modelo

**Prophet (D+1/D+7)**:
- ✅ dbt: Remove colunas tipo "Encerrado", "Resolvido" (sabemos só no futuro)
- ✅ Python: Split temporal (treina em 2024, testa em 2025)

**XGBoost Risk**:
- ✅ dbt: Remove Status final, KPI_Violado (saberíamos o resultado!)
- ✅ Python: Split aleatório (80% treino / 20% teste)
- ✅ MinMaxScaler: aplicado APÓS split

**K-Means**:
- ✅ dbt: Features narrativas (dia da semana, horário)
- ✅ Python: Normalização pós-split, random_state=42

---

## Sprints

| Sprint | Entrega | Data |
|---|---|---|
| Sprint 1 | Ideação e proposta | 
| Sprint 2 | Arquitetura + EDA + Protótipos |
| Sprint 3 | MVP — pipeline + modelos + Power BI | 
| Sprint 4 | Solução final + vídeo pitch | 
---

## ⚙️ Como Executar (Passo a Passo)

### Pré-requisitos

```bash
python --version       # 3.11+
git --version
aws --version          # 2.x
terraform --version    # 1.7+
dbt --version          # 1.8+
apache-airflow         # 2.7+ (via VPS Coolify)
```

### E1-E3: Setup Inicial + Infraestrutura

```bash
# 1. Clonar e criar ambiente
git clone https://github.com/<usuario>/aiops-locaweb.git
cd aiops-locaweb
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configurar credenciais
cp .env.example .env
# Editar .env com AWS + Azure

# 3. Criar infraestrutura AWS
cd infra/terraform
terraform init
terraform apply -var="rds_password=SuaSenha123!"
cd ../..
```

### E4: Bronze (Ingestão XLSX)

```bash
# 1. Colocar LW-DATASET.xlsx em data/raw/
# 2. Upload para S3 Bronze
python pipeline/bronze/upload_xlsx.py

# 3. Validar: S3 deve ter s3://aiops-locaweb-2026/bronze/incidents_standardized.parquet
aws s3 ls s3://aiops-locaweb-datalake-2026/bronze/
```

### E5: Silver (Apache Glue)

```bash
# 1. Testes locais (pytest)
pytest pipeline/silver/test_transformations.py -v

# 2. Upload scripts para S3
aws s3 cp pipeline/silver/*.py s3://aiops-locaweb-datalake-2026/scripts/glue/

# 3. Criar Job Glue via Terraform
cd infra/terraform
terraform apply -target=aws_glue_job.transform_bronze_to_silver
cd ../..

# 4. Executar job (manual)
aws glue start-job-run --job-name transform_bronze_to_silver

# 5. Monitorar
aws logs tail /aws/glue/transform_bronze_to_silver --follow

# 6. Validar output: S3 silver deve ter 41.4k registros
# s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet/Ano_Mes=2025-01/...
```

### E5: EDA + Validação

```bash
# Abrir notebook interativo
jupyter notebook

# Executar: notebooks/02_exploratory_data_analysis_silver.ipynb
# Valida:
#   - Distribuição de registros por tipo
#   - Análise de nulos
#   - Justificação de filtros (por que 41.4k é correto?)
#   - Estatísticas de violação de SLA (1.4%)
```

### E6-E7: dbt (Transformações SQL)

```bash
cd dbt/aiops_locaweb

# 1. Testar conexão RDS
dbt debug

# 2. Executar models Silver (regras KPI)
dbt run --select silver

# 3. Testar
dbt test --select silver

# 4. Executar models Gold (Star Schema + ML features)
dbt run --select gold
dbt test --select gold

# 5. Gerar documentação
dbt docs generate

# Output esperado:
#   - RDS PostgreSQL (schema: public)
#   - Tables: dim_data, dim_prioridade, fact_incidents_kpi
#   - Views: vw_painel_geral, vw_alertas_sla, vw_volume_temporal
#   - Gold/ML tables: features limpas, sem data leakage
```

### E8: Modelos ML + MLflow

```bash
# 1. Feature Engineering (Python - pós split)
jupyter notebook
# Executar: notebooks/04_feature_engineering_ml_training.ipynb

# 2. Prophet D+1/D+7
# Executar: notebooks/05_model_forecast_prophet.ipynb
# Output: MLflow metrics (MAPE, RMSE)

# 3. XGBoost Risk + SHAP
# Executar: notebooks/06_model_risk_xgboost_shap.ipynb
# Output: MLflow metrics (AUC-ROC, SHAP feature importance)

# 4. K-Means Clustering
# Executar: notebooks/07_model_clustering_kmeans.ipynb
# Output: MLflow metrics (Silhouette Score), cluster labels

# Ver resultados:
mlflow ui
# Abrir: http://localhost:5000
```

### E9: Airflow (Orquestração Diária)

```bash
# Setup no VPS Coolify:
#   - DAG: airflow/dags/aiops_pipeline_dag.py
#   - Schedule: diário às 2:00 AM (após encerramento do dia anterior)
#   - Fluxo: Glue → dbt → Python/MLflow → Power BI update

# Testar localmente:
airflow db init
airflow dags test aiops_pipeline $(date +%Y-%m-%d)
```

### E10: Power BI (Serving)

```bash
# 1. Conectar Power BI Desktop ao RDS (Gold/BI schema)
#   - Server: <RDS_ENDPOINT>
#   - Database: aiops
#   - Tables: fact_incidents_kpi, dim_*, vw_painel_geral, vw_alertas_sla

# 2. Criar 4 páginas:
#   1. Painel Geral (KPIs: volume previsto vs real, taxa violação)
#   2. Alertas SLA (incidentes em risco, SHAP feature importance)
#   3. Clusters (distribuição A/B/C/D, padrões)
#   4. Temporal (séries D+1/D+7, tendências)

# 3. Publicar via Microsoft Fabric
# 4. Compartilhar link público
```

### Variáveis de ambiente necessárias

```bash
# AWS
AWS_PROFILE=aiops-project
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=aiops-locaweb-datalake-2026
RDS_HOST=<endpoint>.rds.amazonaws.com
RDS_DB=aiops
RDS_USER=admin
RDS_PASSWORD=<from-terraform>

# Azure ML / MLflow
AZURE_SUBSCRIPTION_ID=<seu-id>
AZURE_RESOURCE_GROUP=<seu-rg>
AZURE_ML_WORKSPACE=<seu-workspace>
AZURE_TENANT_ID=<seu-tenant>
AZURE_CLIENT_ID=<seu-client-id>
AZURE_CLIENT_SECRET=<seu-secret>
MLFLOW_TRACKING_URI=azureml://...

# dbt
DBT_PROFILES_DIR=~/.dbt
```

---

## 🎯 Decisões Arquiteturais Críticas

### Por que dbt para regras de negócio?

```
❌ Alternativa: aplicar filtros em Python
   - Difícil de rastrear historicamente
   - Sem versionamento claro (qual versão do script gerou este dado?)
   - Difícil de testar (qual regra é qual?)
   - Sem auditoria (quem mudou? quando?)

✅ dbt: SQL versionado + testado
   - Git history mostra exatamente quando/por quem mudou
   - dbt test garante que "Exige_Intervencao=1" é correto
   - Reutilizável em múltiplos contextos (BI, ML, etc)
   - Executável em produção (Airflow) com logging automático
```

### Por que Python APÓS split para transformações matemáticas?

```
❌ Alternativa: aplicar MinMaxScaler em dbt (pré-split)
   - Escala do conjunto de teste vazaria para o treino
   - Métricas de teste seriam overly optimistic
   - Modelo parece melhor do que realmente é
   - Em produção, MinMaxScaler diferente destruiria acurácia

✅ Python: split ANTES de normalizar
   - Treino aprende a escala do próprio conjunto (80%)
   - Teste é avaliado com essa escala (20%)
   - MinMaxScaler não vaza informação entre conjuntos
   - Produção: usa sklearn.joblib para reutilizar o mesmo scaler
```

### Por que 3 camadas de proteção contra data leakage?

```
Layer 1: Seleção de Features (dbt)
   └─ Exclui Status final, Resolvido, KPI_Violado (saberíamos o resultado!)

Layer 2: Split Treino/Teste (Python)
   └─ Dados de 2024 não vazam para 2025 (Prophet temporal)
   └─ 80% treino / 20% teste aleatório (XGBoost, K-Means)

Layer 3: Transformações Matemáticas Pós-Split (Python)
   └─ MinMaxScaler: aprendido no treino, aplicado em teste e produção
   └─ One-Hot Encoding: feito APÓS split
   └─ PCA (se necessário): ajustado no treino, transformado em teste
```

---

## 📊 Critérios de Avaliação (Banca Locaweb)

| Critério | Como atendemos |
|---|---|
| **Clareza do problema** | README com arquitetura clara + decisões justificadas |
| **Qualidade da EDA** | Notebook 02 com análise + validação de regras KPI |
| **Separação dbt/Python** | dbt: regras → SQL testável; Python: matemática → modelos reproduzíveis |
| **Proteção Data Leakage** | 3 camadas: features, split, transformações |
| **Antecipação D+1/D+7** | Prophet com intervalo de confiança (MLflow) |
| **Explicabilidade** | SHAP values para risco de OLA, cluster descriptions para K-Means |
| **Geração de valor** | Recomendações operacionais (4 clusters, alertas SLA, forecast) |
| **Reproducibilidade** | Git versionado (dbt SQL, Python com random_state, MLflow artifacts) |
| **Storytelling executivo** | Power BI Fabric com 4 dashboards integrados |

---

## 📚 Documentação Adicional

- **[CLAUDE.md](CLAUDE.md)** — Setup detalhado, troubleshooting, comandos por épico
- **[docs/ARQUITETURA_NOTEBOOKS.md](docs/ARQUITETURA_NOTEBOOKS.md)** — Mapa completo de cada notebook e responsabilidades
- **[docs/TERRAFORM_MODULARIZADO.md](docs/TERRAFORM_MODULARIZADO.md)** — Infraestrutura IaC
- **[md/PLANO_GLUE_SILVER_PARQUET.md](md/PLANO_GLUE_SILVER_PARQUET.md)** — Blueprint detalhado do Glue Job
- **[pipeline/silver/README.md](pipeline/silver/README.md)** — Como usar o módulo Silver localmente

---

## 🚀 Status Atual

- ✅ **E1-E4**: Completos (ambiente, repo, infra, bronze, EDA)
- 🔄 **E5**: Glue Job implementado, aguardando testes em AWS
- ⏳ **E6-E10**: Planejado, aguardando E5 completo

---

*FIAP Challenge 2026 · Locaweb · AIOps Preditivo*  
*Arquitetura: dbt (regras de negócio) + Python (operações matemáticas) = proteção contra data leakage*