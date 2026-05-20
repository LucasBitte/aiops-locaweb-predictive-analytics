# Roadmap de Notebooks: Estrutura Clara e Progressiva

**Objetivo**: Cada nome de notebook deve deixar claro:
1. A sequência (01, 02, 03...)
2. O objetivo da análise/transformação
3. O épico que pertence
4. A camada do data lake (Bronze, Silver, Gold)

---

## Esquema de Renomeação

### Atual (Confuso) → Proposto (Claro)

| # | Atual | Proposto | Épico | Camada | Responsabilidade |
|---|---|---|---|---|---|
| 1 | `01_ingestao.ipynb` | `01_pre_processamento_bronze.ipynb` | E4 | Bronze | Upload XLSX → S3 Bronze |
| 2 | `02_eda_silver.ipynb` | `02_exploratory_data_analysis_silver.ipynb` | E5 | Silver | EDA + validação KPI |
| 3 | ❌ `03_dbt_star_schema_ml_marts.ipynb` | ✅ `03_dbt_transform_silver_to_gold_marts.ipynb` | E6-E7 | Gold | dbt: regras SQL + star schema |
| 4 | ❌ `03_feature_engineering.ipynb` | ✅ `04_feature_engineering_ml_training.ipynb` | E7-E8 | Gold/ML | Python: math após split treino/teste |
| 5 | `04_modelo_forecast.ipynb` | `05_model_forecast_prophet.ipynb` | E8 | Gold/ML | Prophet: D+1/D+7 |
| 6 | `05_modelo_ola_risk.ipynb` | `06_model_risk_xgboost_shap.ipynb` | E8 | Gold/ML | XGBoost + SHAP: risco OLA |
| 7 | `06_clusterizacao.ipynb` | `07_model_clustering_kmeans.ipynb` | E8 | Gold/ML | K-Means: 4 padrões |
| 8 | ➕ NEW | `08_model_workload_forecast_by_team.ipynb` | E8 | Gold/ML | Prophet: forecast por equipe |
| 9 | ➕ NEW | `09_model_anomaly_detection_isolation_forest.ipynb` | E8 | Gold/ML | Isolation Forest: detecção de anomalias |
| 10 | ➕ NEW | `10_model_xgboost_v2_tuned.ipynb` | E8 | Gold/ML | XGBoost v2: tuned + feature selection |

**Problema resolvido**: Não havia dois notebooks `03` (confundiam-se). Agora numeração sequencial 01→10.

---

## Detalhamento por Notebook

### 01: Bronze → Standardization

```
Notebook: 01_pre_processamento_bronze.ipynb
Épico: E4
Camada: Bronze Input
Objetivo: Converter XLSX em CSV, validar schema, upload S3
```

**O que faz**:
- Lê LW-DATASET.xlsx (local)
- Valida coluna de data, tipos
- Converte para CSV + Parquet
- Upload para S3 Bronze
- Gera metadata.json (timestamp, rowcount, MD5)

**Output esperado**:
- s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet
- 122.543 registros, 19 colunas

**Justificativa do nome**:
- `01`: primeira etapa (ingestão)
- `pre_processamento_bronze`: deixa claro que é "antes" (pre) da análise
- `bronze`: a camada de dados

---

### 02: Exploratory Data Analysis (Silver Candidato)

```
Notebook: 02_exploratory_data_analysis_silver.ipynb
Épico: E5
Camada: Silver (análise)
Objetivo: Entender distribuições, validar regras KPI, justificar filtros
```

**O que faz**:
1. **Carrega Bronze** (122.543 incidentes brutos)
2. **Explora**:
   - Distribuição por tipo, prioridade, data
   - Análise de nulos
   - Anomalias
3. **Aplica filtros** (mentalmente):
   - Status = 'Aberto' ou 'Encerrado'
   - Data >= 2025-01-01
4. **Valida KPI**:
   - Por que 41.4k registros é correto?
   - Por que exclusões (A/B/C/D tipos) fazem sentido?
5. **Documenta**:
   - Justificativa de cada regra
   - Estatísticas de violação SLA
   - Impacto de cada filtro

**Output esperado**:
- Gráficos de distribuição
- Tabelas de validação KPI
- Conclusão: "41.4k registros elegíveis para modelagem"

**Justificativa do nome**:
- `02`: segunda etapa (após ingestão)
- `exploratory_data_analysis`: nome padrão em Data Science (EDA)
- `silver`: candidatos a Silver (ainda sem transformação automática)

---

### 03: dbt Transform Silver → Gold Marts

```
Notebook: 03_dbt_transform_silver_to_gold_marts.ipynb
Épico: E6-E7
Camada: Silver (input) → Gold (output)
Objetivo: Documentar e executar modelos dbt
```

**O que faz**:
1. **Executa dbt**:
   ```bash
   dbt run --select silver
   dbt run --select gold
   ```

2. **Documenta** (no notebook):
   - Models criados (staging, silver, gold)
   - SQL de cada modelo
   - Testes (unique, not_null, relationships)

3. **Valida**:
   - Registros em cada stage
   - Colunas esperadas em Gold
   - Partições criadas

4. **Mostra**:
   - Star Schema: dims + fact tables
   - Exemplo de queries em RDS

**Output esperado**:
- RDS PostgreSQL schema: staging, silver, gold
- Gold/BI: fact_incidents_kpi, dim_data, dim_prioridade, vw_painel_geral
- Gold/ML: aggregated features sem data leakage

**Justificativa do nome**:
- `03`: terceira etapa (após EDA)
- `dbt_transform`: deixa claro que é transformação dbt (não Python)
- `silver_to_gold_marts`: origem e destino explícitos

---

### 04: Feature Engineering + ML Training Prep

```
Notebook: 04_feature_engineering_ml_training.ipynb
Épico: E7-E8
Camada: Gold/ML
Objetivo: Preparar dados para treino (split, normalização)
```

**O que faz**:
1. **Carrega Gold/ML** (limpo pelo dbt, sem leakage)
2. **Split treino/teste**:
   ```python
   train, test = train_test_split(data, test_size=0.2, random_state=42)
   ```

3. **Feature Engineering** (APÓS split):
   - MinMaxScaler: ajusta em treino, aplica em teste
   - One-Hot Encoding: aprendido em treino, aplicado em teste
   - Interaction features (se necessário)

4. **Validações**:
   - Nenhuma informação de teste vazou para treino?
   - Distribuições esperadas?
   - Nulos tratados?

5. **Salva** em Gold/ML:
   - X_train, y_train
   - X_test, y_test
   - Scaler (joblib)

**Output esperado**:
- Datasets prontos para treino
- Scaler serializado (`.joblib`)
- Estatísticas de treino vs teste

**Justificativa do nome**:
- `04`: quarta etapa (após dbt)
- `feature_engineering`: técnicas de Features
- `ml_training`: deixa claro que é preparação para treino, não exploração

**CRÍTICO**: Este notebook é DEPOIS do split. Se fosse antes (em dbt), seria data leakage.

---

### 05: Prophet D+1/D+7 Forecast

```
Notebook: 05_model_forecast_prophet.ipynb
Épico: E8
Camada: Gold/ML
Objetivo: Treinar Prophet, logar métricas em MLflow
```

**O que faz**:
1. **Carrega** X_train, y_train do notebook 04
2. **Treina Prophet**:
   ```python
   model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
   model.fit(df_train)
   ```
3. **Avalia em teste** (MAPE, RMSE)
4. **Loga em MLflow**:
   ```python
   mlflow.log_metric("mape_test", mape)
   mlflow.log_artifact("forecast_plot.png")
   ```
5. **Produção**: forecast D+1 e D+7

**Output esperado**:
- Gráficos de forecast
- MLflow metrics (MAPE, RMSE)
- Modelo serializado

**Justificativa do nome**:
- `05`: quinta etapa (primeira modelagem)
- `model_forecast`: deixa claro que é modelagem (não exploração)
- `prophet`: algoritmo específico

---

### 06: XGBoost Risk + SHAP Explainability

```
Notebook: 06_model_risk_xgboost_shap.ipynb
Épico: E8
Camada: Gold/ML
Objetivo: Treinar XGBoost para risco de OLA, explicar com SHAP
```

**O que faz**:
1. **Carrega** X_train, y_train (features pré-processadas)
2. **Treina XGBoost**:
   ```python
   model = XGBClassifier(max_depth=5, n_estimators=100, random_state=42)
   model.fit(X_train, y_train)
   ```
3. **Avalia em teste** (AUC-ROC, PR-AUC)
4. **SHAP values**:
   ```python
   explainer = shap.TreeExplainer(model)
   shap_values = explainer.shap_values(X_test)
   ```
5. **Loga em MLflow**:
   ```python
   mlflow.log_metric("auc_roc_test", auc_roc)
   mlflow.log_artifact("shap_plot.png")
   ```

**Output esperado**:
- Gráficos SHAP (feature importance)
- MLflow metrics (AUC-ROC)
- Modelo serializado

**Justificativa do nome**:
- `06`: sexta etapa
- `model_risk`: deixa claro que é risco (não forecast)
- `xgboost_shap`: algoritmo + técnica de explicação

---

### 07: K-Means Clustering

```
Notebook: 07_model_clustering_kmeans.ipynb
Épico: E8
Camada: Gold/ML
Objetivo: Agrupar em 4 clusters, interpretar padrões
```

**O que faz**:
1. **Carrega** X_train (features narrativas/temporais)
2. **Treina K-Means**:
   ```python
   kmeans = KMeans(n_clusters=4, random_state=42)
   kmeans.fit(X_train)
   ```
3. **Avalia** (Silhouette Score, Inertia)
4. **Interpreta** 4 clusters:
   - Cluster A: críticos prolongados
   - Cluster B: recorrentes rápidos
   - Cluster C: sazonais
   - Cluster D: baixo impacto
5. **Loga em MLflow**:
   ```python
   mlflow.log_metric("silhouette_score", silhouette)
   mlflow.log_artifact("cluster_interpretation.txt")
   ```

**Output esperado**:
- Gráficos de clusters
- Interpretação de cada cluster
- MLflow metrics

**Justificativa do nome**:
- `07`: sétima etapa
- `model_clustering`: deixa claro que é agrupamento (não classificação)
- `kmeans`: algoritmo específico

---

## Convenção de Nomenclatura

```
<número>_<objetivo>_<tipo_ou_metodo>.ipynb

Onde:
  <número>: 01-07 (ordem sequencial)
  <objetivo>: o que o notebook busca fazer (eda, preprocessing, model, etc)
  <tipo_ou_metodo>: tecnologia/algoritmo (bronze, silver, prophet, xgboost, etc)
```

### Exemplos de padrão

✅ Bom:
- `01_pre_processamento_bronze.ipynb` — claro: prep + bronze
- `02_exploratory_data_analysis_silver.ipynb` — claro: EDA + silver
- `05_model_forecast_prophet.ipynb` — claro: model + forecast + Prophet

❌ Ruim:
- `03_feature_engineering.ipynb` — ambíguo: é dbt ou Python?
- `04_modelo_forecast.ipynb` — português misturado + vago (qual modelo?)
- `notebook_analise.ipynb` — sem número, sem sequência

---

## Implementação

### Passo 1: Renomear os arquivos

```bash
# E5: Silver
git mv notebooks/02_eda_silver.ipynb notebooks/02_exploratory_data_analysis_silver.ipynb

# E6-E7: dbt
git mv notebooks/03_dbt_star_schema_ml_marts.ipynb notebooks/03_dbt_transform_silver_to_gold_marts.ipynb

# E7-E8: Python ML
git mv notebooks/03_feature_engineering.ipynb notebooks/04_feature_engineering_ml_training.ipynb
git mv notebooks/04_modelo_forecast.ipynb notebooks/05_model_forecast_prophet.ipynb
git mv notebooks/05_modelo_ola_risk.ipynb notebooks/06_model_risk_xgboost_shap.ipynb
git mv notebooks/06_clusterizacao.ipynb notebooks/07_model_clustering_kmeans.ipynb
```

### Passo 2: Atualizar referências

- README.md ✅ (já atualizado)
- CLAUDE.md ✅ (já atualizado)
- docs/ARQUITETURA_NOTEBOOKS.md ✅ (já atualizado)

### Passo 3: Commit

```bash
git add notebooks/ docs/ README.md CLAUDE.md
git commit -m "docs(e5-e8): renomear notebooks para deixar claro objetivo de cada um

- 02: EDA + validação KPI (Silver)
- 03: dbt transforms (Silver→Gold)
- 04: Feature engineering pós-split (Python)
- 05-07: Modelos (Prophet, XGBoost, K-Means)

Convenção: <número>_<objetivo>_<método>.ipynb
"
```

---

### 08: Prophet Workload Forecast per Team

```
Notebook: 08_model_workload_forecast_by_team.ipynb
Épico: E8
Camada: Gold/ML
Objetivo: Prever volume de incidentes por equipe (responder "quais equipes podem sobrecarregar?")
```

**O que faz**:
1. **Carrega** histórico diário agregado por equipe (grupo_designado)
2. **Filtra** equipes com >= 60 dias de histórico
3. **Treina Prophet independente** para cada equipe:
   ```python
   for team in teams:
       model = Prophet(weekly_seasonality=True)
       model.fit(df_team)
   ```
4. **Avalia** cada modelo com MAPE em holdout de 30 dias
5. **Loga em MLflow** nested runs por equipe:
   - team name + n_days + MAPE para cada run filho
6. **Forecast D+1 a D+7** segmentado por equipe
7. **Salva** métricas em data/ml/forecast_by_team/forecast_by_team_metrics.csv

**Output esperado**:
- Modelos Prophet por equipe (N=13-15 equipes)
- CSV com equipes, dias de histórico, MAPE
- Forecasts D+1-D+7 para planning de recursos

**Justificativa do nome**:
- `08`: oitava etapa (modelo complementar ao Prophet geral)
- `model_workload_forecast`: deixa claro que é forecast de volume (não risco)
- `by_team`: segmentação por equipe

---

### 09: Anomaly Detection with Isolation Forest

```
Notebook: 09_model_anomaly_detection_isolation_forest.ipynb
Épico: E8
Camada: Gold/ML
Objetivo: Detectar incidentes anômalos fora dos padrões normais
```

**O que faz**:
1. **Carrega** features de incidentes (duração, SLA violation %, reabertas, comentários, etc)
2. **Normaliza** features com StandardScaler
3. **Treina Isolation Forest**:
   ```python
   model = IsolationForest(contamination=0.05, random_state=42)
   labels = model.fit_predict(X_scaled)
   ```
4. **Gera anomaly scores** para cada incidente (mais negativo = mais anômalo)
5. **Visualização PCA 2D** de anomalias vs normais
6. **Distribuição de scores** com threshold marcado
7. **Loga em MLflow**:
   - n_anomalies_detected, pct_anomalies, mean/std anomaly_score
   - Artefatos: scaler, modelo, plots (PCA, scores distribution)
8. **Salva** anomalias detectadas para investigação

**Output esperado**:
- Incidentes anômalos identificados (~5% do total)
- CSV com incidentes anômalos para análise
- Visualizações em MLflow para exploração

**Justificativa do nome**:
- `09`: nona etapa (modelo complementar para alertas)
- `model_anomaly_detection`: deixa claro que é detecção de outliers
- `isolation_forest`: algoritmo específico

**Use Case**: Complementa K-Means (agrupa normais) + Isolation Forest (detecta anômulos)

---

### 10: XGBoost v2 Tuned & Optimized

```
Notebook: 10_model_xgboost_v2_tuned.ipynb
Épico: E8
Camada: Gold/ML
Objetivo: Modelo XGBoost otimizado e pronto para produção
```

**O que faz**:
1. **Carrega** features de risco do dataset
2. **Preprocessing** (StandardScaler + OneHotEncoder)
   - Treina em X_train, aplica em X_test (sem leakage)
3. **Baseline XGBoost** com best params encontrados:
   ```python
   model = XGBClassifier(max_depth=6, learning_rate=0.1, n_estimators=100)
   ```
4. **SHAP-based Feature Selection**:
   - Calcula SHAP importance para 598 features
   - Seleciona top features (threshold=0.005)
   - Reduz para ~50-80 features (87% redução)
   - Retreina com features selecionadas
5. **Threshold Optimization**:
   - Precision-Recall curve para maximizar F1-score
   - Encontra threshold ótimo (não padrão 0.5)
6. **StratifiedKFold Cross-Validation**:
   - 5 folds com validação robusta
   - Log de AUC-ROC por fold
7. **Artefatos logados** em MLflow:
   - Modelo serializado (.pkl)
   - Preprocessor (StandardScaler + OneHotEncoder)
   - Feature selection mask (quais features usar)
   - Plots: ROC curves comparison + threshold optimization

**Output esperado**:
- Modelo XGBoost v2 com 87% menos features
- Performance: AUC-ROC > 0.97, F1 otimizado
- Threshold ótimo para decisão
- Tudo serializado e pronto para serving

**Justificativa do nome**:
- `10`: décima etapa (refinamento do 06)
- `model_xgboost_v2`: deixa claro que é versão 2 (melhorada vs 06)
- `tuned`: hyperparameters otimizados

**Melhoria vs Notebook 06**:
- ✅ Feature selection automática (87% redução)
- ✅ Threshold optimization para F1-score
- ✅ Cross-validation robusta
- ✅ Feature selection mask salvo (reproduzível em produção)

---

## Status por Notebook

| # | Nome | Status | Próximo Passo |
|---|---|---|---|
| 01 | Pre-processamento Bronze | ✅ Pronto | (já executado) |
| 02 | EDA Silver | ✅ Pronto | Executar e validar |
| 03 | dbt Transform | ✅ Pronto | (já executado) |
| 04 | Feature Engineering | ✅ Pronto | (já executado) |
| 05 | Prophet Forecast | ✅ Pronto + CV | Executar e validar |
| 06 | XGBoost Risk | ✅ Pronto + Tuning | Executar e validar |
| 07 | K-Means Clustering | ✅ Pronto + MLflow | Executar e validar |
| 08 | Prophet per Team | ✅ Criado | Executar e validar |
| 09 | Anomaly Detection | ✅ Criado | Executar e validar |
| 10 | XGBoost v2 Tuned | ✅ Criado | Executar e validar |

---

**Data**: 2026-05-20  
**Épico**: E5-E8  
**Objetivo**: Deixar claro a sequência, responsabilidade e tecnologia de cada notebook

---

## Atualizações E8 - ML Improvements

**2026-05-20**: Adicionados notebooks 08-10 como resultado do plano de melhoria ML (Part 3):
- `08_model_workload_forecast_by_team.ipynb` — Prophet por equipe
- `09_model_anomaly_detection_isolation_forest.ipynb` — Detecção de anomalias
- `10_model_xgboost_v2_tuned.ipynb` — XGBoost otimizado para produção

Todos com MLflow comprehensive tracking conforme Part 2-3 do plano.
