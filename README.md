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
| Transformação | Python · Pandas · dbt |
| Modelagem | Prophet · XGBoost · K-Means · SHAP |
| Tracking | MLflow · Azure ML Studio |
| Orquestração | Apache Airflow (VPS Coolify) |
| Serving | Power BI · Microsoft Fabric |

---

## Arquitetura

```
LW-DATASET.xlsx (local)
        │
        ▼
┌─────────────────────────────────────────────────┐
│               AWS S3 — Data Lake                │
│  bronze/   → CSV bruto original                 │
│  silver/   → 25.600 incidentes elegíveis KPI    │
│  gold/ml/  → features para 3 modelos            │
│  gold/bi/  → Star Schema para Power BI          │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
  Azure ML Studio        RDS PostgreSQL
  Prophet  D+1/D+7       Star Schema
  XGBoost  OLA Risk      Power BI Fabric
  K-Means  Clusters
```

---

## 📋 Épicos do Projeto

| # | Épico | Descrição |
|---|---|---|
| E1 | **Ambiente Local** | VS Code + Python + Git + AWS CLI + MLflow configurados |
| E2 | **Repositório GitHub** | Estrutura do projeto versionada |
| E2 | **Infraestrutura AWS** | S3 + RDS + IAM via Terraform |
| E2 | **Bronze** | Upload do LW-DATASET.xlsx convertido para S3 |
| E3 | **EDA** | Análise exploratória completa com validação das regras KPI |
| E4 | **Silver** | Limpeza, filtragem e feature engineering com dbt |
| E5 | **Gold** | Features para ML + Star Schema histórico para Power BI |
| E6 | **Modelos** | Prophet + XGBoost + K-Means com MLflow/Azure ML tracking |
| E7 | **Airflow** | Orquestração do pipeline completo via VPS |
| E80 | **Serving** | Power BI Fabric com 4 páginas analíticas |

---

## Estrutura de Pastas

```
aiops-locaweb/
├── infra/terraform/          # Terraform: S3, RDS, IAM
├── notebooks/
│   ├── 01_ingestao.ipynb
│   ├── 02_eda_silver.ipynb
│   ├── 03_feature_engineering.ipynb
│   ├── 04_modelo_forecast.ipynb
│   ├── 05_modelo_ola_risk.ipynb
│   └── 06_clusterizacao.ipynb
├── pipeline/
│   ├── setup/                # Criar estrutura S3
│   ├── bronze/               # Upload XLSX → S3
│   ├── silver/               # Limpeza e filtragem
│   └── gold/                 # Features ML
├── dbt/aiops_locaweb/        # Modelos dbt (Silver + Gold)
├── airflow/dags/             # DAG de orquestração
└── data/                     # Local — não versionado
```

---

## Modelos Preditivos

| Modelo | Algoritmo | Target | Métrica |
|---|---|---|---|
| Forecast D+1 | Prophet | Volume diário total | MAPE |
| Forecast D+7 | Prophet | Volume médio semanal | MAPE |
| Risco de OLA | XGBoost + SHAP | KPI violado (0/1) | AUC-ROC |
| Padrões | K-Means | Cluster A/B/C/D | Silhouette |

**4 clusters identificados:**
- **A — Críticos prolongados** — Infraestrutura, P2, segunda-feira, alto OLA
- **B — Recorrentes rápidos** — BD/App, P3, diário, baixo OLA
- **C — Sazonais previsíveis** — início de mês, padrão claro
- **D — Baixo impacto** — Storage, P3, fim de semana

---

## Sprints

| Sprint | Entrega | Data |
|---|---|---|
| Sprint 1 | Ideação e proposta | 
| Sprint 2 | Arquitetura + EDA + Protótipos |
| Sprint 3 | MVP — pipeline + modelos + Power BI | 
| Sprint 4 | Solução final + vídeo pitch | 
---

## Como Executar

### Pré-requisitos

```bash
python --version    # 3.11+
git --version
aws --version       # 2.x
terraform --version # 1.7+
```

### Setup inicial

```bash
# 1. Clonar e criar ambiente
git clone https://github.com/<usuario>/aiops-locaweb.git
cd aiops-locaweb
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configurar credenciais
cp .env.example .env
# Editar .env com suas credenciais AWS e Azure

# 3. Criar infraestrutura AWS
cd infra/terraform
terraform init
terraform apply -var="rds_password=SuaSenha123!"

# 4. Criar estrutura S3 (teste de conexão)
python pipeline/setup/criar_estrutura_s3.py

# 5. Upload do dataset
# Colocar LW-DATASET.xlsx em data/raw/
python pipeline/bronze/upload_xlsx.py

# 6. EDA e Silver
jupyter notebook
# Abrir: notebooks/02_eda_silver.ipynb
```

### Variáveis de ambiente necessárias

```bash
# AWS
AWS_PROFILE=aiops
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET=aiops-locaweb-<account-id>
RDS_HOST=<endpoint>.rds.amazonaws.com
RDS_DB=aiops
RDS_USER=admin
RDS_PASSWORD=

# Azure ML
AZURE_SUBSCRIPTION_ID=
AZURE_RESOURCE_GROUP=
AZURE_ML_WORKSPACE=
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
MLFLOW_TRACKING_URI=azureml://...
```

---

## Critérios de Avaliação (Banca Locaweb)

| Critério | Como atendemos |
|---|---|
| Clareza do problema | README + slide objetivo |
| Qualidade da EDA | Notebook 02 com análise completa |
| Coerência da modelagem | MLflow/Azure ML com comparação de runs |
| Antecipação D+1/D+7 | Prophet com intervalo de confiança |
| Geração de valor | Recomendações práticas operacionais |
| Storytelling executivo | Power BI Fabric com 4 páginas analíticas |



*FIAP Challenge 2026 · Locaweb · AIOps*