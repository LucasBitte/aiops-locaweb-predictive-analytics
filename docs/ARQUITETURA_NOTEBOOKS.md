# 📚 Arquitetura de Notebooks: Mapa de Responsabilidades e Fluxo de Dados

**Data**: 2026-05-18  
**Projeto**: AIOps Locaweb (E5 - Analytics Exploratória)  
**Propósito**: Documentar o papel, fluxo e dependências entre notebooks

---

## 🗺️ Visão Geral: O Mapa Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│ DATA LAKE MEDALLION ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────┘

           INPUT: XLSX Local              
              (LW-DATASET.xlsx)           
                     │                    
                     ↓                    
  ┌──────────────────────────────────────────┐                        
  │ 01_pre_processamento_bronze.ipynb        │ ← CRIAR BRONZE         
  │ (E4: Bronze Layer)                       │                        
  │ ├─ Ler: XLSX local                       │                        
  │ ├─ Transformar: tipos, encoding          │                        
  │ └─ Salvar: S3 Bronze Parquet             │                        
  └──────────────────────────────────────────┘                        
                     │                    
                     ↓                    
        s3://aiops-locaweb-datalake-2026/     
        bronze/incidents_standardized.parquet 
        (122.543 registros, 19 colunas)      
                     │                    
    ┌────────────────┴────────────────┐     
    ↓                                 ↓     
┌──────────────────┐      ┌──────────────────────────────────┐
│ 02_eda_silver    │      │ 04_bronze_silver_transformacao   │
│ .ipynb           │      │ .ipynb                           │
│ (Exploratório)   │      │ (Prático + Validações)           │
│                  │      │                                  │
│ ├─ EDA           │      │ ├─ Filtros (Status, Data)        │
│ ├─ Nulos         │      │ ├─ 6 Features engineered         │
│ ├─ Distribuições │      │ ├─ Tratamento de nulos          │
│ └─ Amostra       │      │ ├─ Target_Risco_SLA             │
│                  │      │ ├─ Validações                   │
└──────────────────┘      │ └─ Salvar: S3 Silver Parquet     │
                          └──────────────────────────────────┘
    (Entendimento)                  │
                                    ↓
                    s3://aiops-locaweb-datalake-2026/
                    silver/incidents_silver_2025.parquet
                    (41.441 registros, 25 colunas)
                                    │
                    ┌───────────────┘
                    │
                    ↓
        ┌──────────────────────────────────────────┐
        │ 03_dbt_star_schema_ml_marts.ipynb        │ ← DBT + RDS
        │ (E6-E7: Data Warehouse)                  │
        │                                          │
        │ ├─ Ler: Silver Parquet                   │
        │ ├─ dbt run: Dimensões + Fatos            │
        │ └─ Salvar: RDS PostgreSQL (Star Schema)  │
        └──────────────────────────────────────────┘
                        │
                        ↓
                PostgreSQL RDS
                (Gold Layer)
            ├─ dim_data, dim_prioridade
            ├─ dim_categoria, dim_grupo
            ├─ fact_incidents_kpi
            └─ vw_painel, vw_alertas
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ↓                               ↓
┌──────────────────────────┐   ┌──────────────────┐
│ 03_feature_              │   │ [E8-E10]         │
│ engineering.ipynb        │   │ ├─ ML Models     │
│ (E7: Gold Features)      │   │ ├─ Airflow (E9)  │
│                          │   │ └─ Power BI(E10) │
│ ├─ df_serie_temporal.csv │   │                  │
│ ├─ df_matriz_risco.csv   │   └──────────────────┘
│ └─ df_perfis_cluster.csv │
└──────────────────────────┘
```

---

## 📋 Tabela Resumida: Responsabilidades

| Notebook | Épico | Tipo | Input | Output | Propósito | Status |
|----------|-------|------|-------|--------|-----------|--------|
| **01_pre_processamento_bronze** | E4 | Ingestão | XLSX local | Bronze Parquet | Standardizar dados brutos | ✅ |
| **02_eda_silver** | E5 | Exploração | Bronze Parquet | Análise + Amostra | Entender distribuições, nulos | ✅ |
| **04_bronze_silver_transformacao** | E5 | Transformação | Bronze Parquet | Silver Parquet | Limpar, enriquecer, validar | 🔄 |
| **03_dbt_star_schema_ml_marts** | E6-E7 | Data Warehouse | Silver Parquet | Gold (RDS) + Star Schema | Dimensões, fatos, views BI | ⏳ |
| **03_feature_engineering** | E7 | Feature Eng | Silver Parquet | 3 CSVs (modelos) | Criar features para ML | ⏳ |
| **[Airflow DAG]** | E9 | Orquestração | - | Pipeline automático | Agendar execuções | ⏳ |

---

## 🔍 Detalhamento por Notebook

---

### 01_pre_processamento_bronze.ipynb

**Épico**: E4  
**Tipo**: Ingestão de Dados  
**Responsabilidade**: Converter XLSX bruto em Bronze Parquet standardizado

#### Input
- **Arquivo**: `LW-DATASET.xlsx` (local)
- **Formato**: Excel
- **Tamanho**: ~50 MB
- **Conteúdo**: 122.543 incidentes, 19 colunas, tipos mistos

#### Processamento
```
XLSX → Validação de schema → Conversão de tipos → Encoding (UTF-8) → Padronização de nomes
```

**Transformações**:
1. **Leitura**: `pd.read_excel()`
2. **Tipos**: Converter string[] para string (pandas nullable), datetime para datetime64
3. **Encoding**: Garantir UTF-8 (caracteres especiais: ç, ã, é)
4. **Nomes de colunas**: Standardizar (remover espaços extras, maiúsculas)
5. **Valores**: Padronizar (ex: "sim"/"não" → "SIM"/"NAO")

#### Output
- **Path**: `s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet`
- **Formato**: Parquet (comprimido, otimizado para leitura)
- **Partições**: Ano/Mês (automático)
- **Registros**: 122.543
- **Colunas**: 19 (nenhuma removida)
- **Metadata**: `metadata.json` (timestamp, rowcount, hash MD5)

#### Validações
```
✅ Schema esperado presente
✅ Sem linhas duplicadas
✅ Tipos convertidos corretamente
✅ Encoding UTF-8 validado
✅ Partições criadas (2018-2026)
```

#### Quando Usar
- Primeira vez que carrega dados do XLSX
- Se houver mudanças no layout do XLSX
- Manutenção anual (validar integridade)

#### Saída para Próximo
→ **02_eda_silver.ipynb** (exploração)  
→ **04_bronze_silver_transformacao.ipynb** (transformação)

---

### 02_eda_silver.ipynb

**Épico**: E5  
**Tipo**: Análise Exploratória (EDA)  
**Responsabilidade**: Entender distribuições, nulos, anomalias, correlações

#### Input
- **Path**: `s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet`
- **Formato**: Parquet
- **Registros**: 122.543
- **Colunas**: 19

#### Processamento
```
Carregar Bronze → Análise Descritiva → Visualizações → Nulos → Distribuições → Anomalias
```

**Análises Realizadas**:
1. **Descritivo**: count, mean, std, min, max, percentis
2. **Nulos**: Percentual por coluna, padrões (por Data? por Produto?)
3. **Categorias**: value_counts() para Status, Prioridade, Produto, etc
4. **Temporais**: Série histórica (volume por mês, por ano)
5. **Correlações**: Prioridade vs Duração? Grupo vs Taxa de violação?
6. **Outliers**: Detecção de durações anômalas, datas fora do padrão

#### Output
- **Gráficos**: Histogramas, boxplots, linhas temporais, heatmaps
- **Tabelas**: Distribuição, nulos, estatísticas
- **Amostra**: Small subset para inspeção manual
- **Insights**: Notas em markdown sobre anomalias, decisões de filtro

#### Validações
```
✅ Não modifica dados (read-only)
✅ Gráficos salvos em ./output/
✅ Insights documentados em células markdown
```

#### Quando Usar
- Antes de fazer transformações (entender dados)
- Quando há dúvida sobre um padrão
- Documentação para stakeholders (mostrar distribuições)
- Validação pós-transformação (comparar Bronze vs Silver)

#### Saída para Próximo
→ **04_bronze_silver_transformacao.ipynb** (informar decisões de filtro)

---

### 04_bronze_silver_transformacao.ipynb

**Épico**: E5  
**Tipo**: Transformação e Enriquecimento  
**Responsabilidade**: Converter Bronze (bruto) em Silver (pronto para ML)

#### Input
- **Path**: `s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet`
- **Formato**: Parquet
- **Registros**: 122.543
- **Colunas**: 19

#### Processamento
```
Carregar → Filtro 1: Status → Filtro 2: Data → Features (6x) → Nulos (fillna) → Target → Validações → Salvar
```

**Transformações Executadas**:

1. **Filtro 1**: `Status != 'Sem Intervenção'`
   - Remove ~81k registros de ruído (monitoramento automático)
   - Mantém apenas esforço real humano
   - Resultado: ~41k registros

2. **Filtro 2**: `Aberto >= 2025-01-01`
   - Remove dados históricos (contexto mudou)
   - Mantém comportamento atual (2025+)
   - Resultado: ~41k registros (coerente com notebook 02)

3. **Features Engineered** (6 derivadas):
   - `Exige_Intervencao` (int 0/1): Flag de esforço real
   - `Prioridade_Num` (int 1-5): Número de prioridade
   - `Possui_Pai` (int 0/1): Flag de incidente filho
   - `Duracao_Horas` (float): Segundos → horas
   - `Data_Abertura` (date): Data sem hora
   - `KPI_Status_Int` (int -1/0/1): KPI codificado com sentinela

4. **Tratamento de Nulos** (regras de negócio):
   - `Produto` → "Não Classificado"
   - `Categoria` → "Não Classificado"
   - `Subcategoria` → "Não Informada"
   - `Incidente_Pai` → "Independente"
   - `Código_de_fechamento` → "Não Encerrado"
   - `Solução` → "Sem Descrição"
   - `Resolvido`, `Encerrado` → **NaT (manter nulo)**

5. **Cálculo do Target** (3 camadas):
   - **Camada 1** (Base): Use KPI_Violado diretamente
   - **Camada 2** (Heurística): Se KPI=?, P2, Duração > 4h → assume violado
   - **Camada 3** (Isenções): Se tem pai OU sem intervenção → não conta

6. **Validações**:
   - Schema esperado presente
   - Nulos críticos = 0
   - Features em ranges válidos
   - Target distribuído (98.6% vs 1.4%)

#### Output
- **Path**: `s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet`
- **Formato**: Parquet particionado por `Ano_Mes` (2025-01, 2025-02, ..., 2025-12)
- **Registros**: 41.441
- **Colunas**: 25 (19 originais + 6 engineered)
- **Metadata**: Logging de transformação, estatísticas, validações

#### Validações
```
✅ Schema: 25 colunas esperadas presentes
✅ Nulos: Colunas críticas = 0 nulos
✅ Features: Ranges validados (Prioridade 1-5, Target 0/1, etc)
✅ Target: Distribuição (98.6% sem risco, 1.4% com risco)
✅ Partições: 12 partições Ano_Mes criadas
✅ Parquet: Integridade verificada (releitura do S3)
```

#### Quando Usar
- Etapa principal de transformação (Silver creation)
- Executado diariamente via Airflow (E9)
- Quando há mudanças em regras de negócio (filtros, features)

#### Saída para Próximo
→ **03_dbt_star_schema_ml_marts.ipynb** (criar star schema no RDS)  
→ **03_feature_engineering.ipynb** (criar features específicas para modelos)

---

### 03_dbt_star_schema_ml_marts.ipynb

**Épico**: E6-E7  
**Tipo**: Data Warehouse + dbt Transformação  
**Responsabilidade**: Criar Star Schema em RDS PostgreSQL a partir de Silver Parquet

#### Input
- **Path**: `s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet`
- **Formato**: Parquet
- **Registros**: 41.441
- **Colunas**: 25 (completas com features Silver)

#### Processamento
```
1. Conectar RDS PostgreSQL via dbt
2. Copiar Silver para RDS (raw_incidents_silver)
3. dbt run: Criar modelos (dimensões e fatos)
4. Validações dbt (unique, not_null, accepted_values)
5. Criar views para BI
```

**Modelos dbt Criados** (Star Schema):

**Dimensões** (lookup tables):
- `dim_data`: Data de abertura (ano, mês, dia, semana, dia_semana)
- `dim_prioridade`: P1-P5 com SLA mapeado
- `dim_categoria`: Categorias de incidentes
- `dim_grupo`: Grupos/equipes responsáveis
- `dim_produto`: Produtos/sistemas impactados
- `dim_cluster`: Clusters resultantes de K-Means (E8)

**Fatos** (fact tables):
- `fact_incidents_kpi`: Cada incidente com FK para dimensões
  - Colunas: incident_id, date_id, priority_id, category_id, group_id, product_id
  - Métricas: duration_hours, kpi_status, target_risco_sla
  
**Views Analytics** (para Power BI):
- `vw_painel_geral`: Overview por prioridade, grupo, produto
- `vw_alertas_sla`: Incidentes em risco de violação
- `vw_volume_temporal`: Volume diário/semanal
- `vw_eficiencia_grupo`: Taxa de sucesso por grupo

#### Output
- **RDS PostgreSQL**: aiops_gold database
  - Schema: `public`
  - Tabelas: `dim_*`, `fact_incidents_kpi`
  - Views: `vw_*`
  
- **Documentação dbt**:
  - `docs/dbt_generated/index.html` (generated)
  - Lineage de transformações
  - Testes executados e passados

#### Transformações Específicas

1. **dim_data** (lê Data_Abertura):
   ```sql
   SELECT DISTINCT
     Date_Abertura as date,
     EXTRACT(YEAR FROM Date_Abertura) as ano,
     EXTRACT(MONTH FROM Date_Abertura) as mes,
     EXTRACT(DAY FROM Date_Abertura) as dia,
     EXTRACT(ISODOW FROM Date_Abertura) as dia_semana,  -- 1=seg, 7=dom
     ...
   FROM raw_incidents_silver
   ```

2. **dim_prioridade** (lê Prioridade_Num):
   ```sql
   SELECT
     Prioridade_Num as priority,
     CASE Prioridade_Num
       WHEN 1 THEN 4    -- P1 = 4 horas
       WHEN 2 THEN 12   -- P2 = 12 horas
       WHEN 3 THEN 24   -- P3 = 24 horas
       WHEN 4 THEN 72   -- P4 = 3 dias
       WHEN 5 THEN 120  -- P5 = 5 dias
     END as sla_horas,
     ...
   FROM raw_incidents_silver
   ```

3. **fact_incidents_kpi** (combina tudo):
   ```sql
   SELECT
     Número as incident_id,
     date_id,  -- FK dim_data
     priority_id,  -- FK dim_prioridade
     category_id,  -- FK dim_categoria
     group_id,  -- FK dim_grupo
     Duracao_Horas as duration_hours,
     Target_Risco_SLA as kpi_status,
     Possui_Pai as has_parent,
     ...
   FROM raw_incidents_silver
   LEFT JOIN dim_data ON Data_Abertura = dim_data.date
   LEFT JOIN dim_prioridade ON Prioridade_Num = dim_prioridade.priority
   ...
   ```

4. **vw_painel_geral** (aggregation view):
   ```sql
   SELECT
     p.priority,
     COUNT(*) as total_incidents,
     SUM(CASE WHEN kpi_status = 1 THEN 1 ELSE 0 END) as violations,
     ROUND(100.0 * SUM(CASE WHEN kpi_status = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as violation_rate
   FROM fact_incidents_kpi f
   LEFT JOIN dim_prioridade p ON f.priority_id = p.id
   GROUP BY p.priority
   ```

#### Validações dbt
```
✅ unique: incident_id (fact_incidents_kpi)
✅ not_null: incident_id, date_id, priority_id (fact)
✅ not_null: priority (dim_prioridade)
✅ accepted_values: priority IN (1,2,3,4,5)
✅ relationships: priority_id refs dim_prioridade.id
```

#### Quando Usar
- Primeira vez: Setup do schema no RDS
- Diariamente (E9): Airflow atualiza facts/dims do Silver
- Quando há mudanças em regras de negócio (SLA mapeado, dimensões)

#### Saída para Próximo
→ **[E8: ML Notebooks]** (leem fact_incidents_kpi para treinar modelos)  
→ **[E10: Power BI]** (conecta a vw_* views para dashboards)

---

### 03_feature_engineering.ipynb

**Épico**: E7 (Gold Layer)  
**Tipo**: Feature Engineering Avançado  
**Responsabilidade**: Criar 3 datasets específicos para modelos distintos

#### Input
- **Path**: `s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet`
- **Formato**: Parquet
- **Registros**: 41.441
- **Colunas**: 25

#### Processamento
```
Carregar Silver → Análise de Dicionário → Transformação específica por modelo → Salvar CSVs
```

**3 Outputs Distintos** (cada um para um modelo diferente):

1. **df_serie_temporal.csv** → Prophet (Forecast D+1/D+7)
   - Agregação: Contagem diária de incidentes abertos
   - Colunas: `Data_Abertura`, `Total_Chamados`
   - Validação: Série contínua (sem gaps > 1 dia)

2. **df_matriz_risco.csv** → XGBoost (Classificação OLA Risk)
   - Nível: 1 linha por incidente
   - Variáveis: Prioridade, Grupo, Categoria, Possui_Pai, **excluindo** Duração/Status (data leakage!)
   - Target: `Target_Risco_SLA`
   - Preprocessamento: SMOTE ou class_weight para desbalanceamento

3. **df_perfis_cluster.csv** → K-Means (Clustering Operacional)
   - Nível: 1 linha por incidente
   - Variáveis: Causas (Grupo, Categoria) + Efeitos (Duracao_Horas, Target) + Estrutura (Possui_Pai)
   - Normalização: MinMaxScaler em Duracao_Horas
   - Encoding: Target Encoding em variáveis categorias

#### Output
- **Path 1**: `s3://aiops-locaweb-datalake-2026/gold/df_serie_temporal.csv`
- **Path 2**: `s3://aiops-locaweb-datalake-2026/gold/df_matriz_risco.csv`
- **Path 3**: `s3://aiops-locaweb-datalake-2026/gold/df_perfis_cluster.csv`

#### Documentação
- **Dicionário de dados**: Mapping de 26 colunas Silver
- **Decisões de design**: Por que excluir Duração em risco? Por que incluir em clustering?
- **Regras de imputação**: Como preencher nulos antes do ML?

#### Quando Usar
- Antes de treinar cada modelo (E8)
- Quando há mudanças em features Silver (atualizar ouro)
- Validação: Comparar distribuições com Silver

#### Saída para Próximo
→ **[04_modelo_forecast.ipynb]** (usar df_serie_temporal)  
→ **[05_modelo_ola_risk.ipynb]** (usar df_matriz_risco)  
→ **[06_clusterizacao.ipynb]** (usar df_perfis_cluster)

---

## 📊 Fluxo de Dados Completo (Mapa Sequencial)

```
┌──────────────────────────────────────────────────────────────────────┐
│ FASE 1: INGESTÃO (E4)                                                │
├──────────────────────────────────────────────────────────────────────┤
│ 01_pre_processamento_bronze.ipynb                                    │
│ Input:  LW-DATASET.xlsx (local)                                      │
│ Output: Bronze Parquet (s3://...bronze/...)                          │
│ Result: 122.543 registros, 19 colunas (padronizados)                │
└──────────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────────┐
│ FASE 2: EXPLORAÇÃO & TRANSFORMAÇÃO (E5)                              │
├──────────────────────────────────────────────────────────────────────┤
│ 02_eda_silver.ipynb (Exploração)                    ← Entender dados │
│ Input:  Bronze Parquet (s3://...bronze/...)                          │
│ Output: Análises, gráficos, insights                                 │
│                                                                       │
│ 04_bronze_silver_transformacao.ipynb (Transform)    ← Limpar dados  │
│ Input:  Bronze Parquet (s3://...bronze/...)                          │
│ Output: Silver Parquet (s3://...silver/...)                          │
│ Result: 41.441 registros, 25 colunas (limpos + features)            │
└──────────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────────┐
│ FASE 3: DATA WAREHOUSE & STAR SCHEMA (E6-E7)                        │
├──────────────────────────────────────────────────────────────────────┤
│ 03_dbt_star_schema_ml_marts.ipynb (dbt + RDS)      ← Star schema    │
│ Input:  Silver Parquet (s3://...silver/...)                          │
│ Output: Gold (RDS PostgreSQL)                                        │
│   └─ Dimensões: dim_data, dim_prioridade, dim_categoria, ...         │
│   └─ Fatos: fact_incidents_kpi                                       │
│   └─ Views: vw_painel_geral, vw_alertas_sla, ...                    │
│ Tools:  dbt (transformação) + PostgreSQL (persistência)              │
└──────────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────────┐
│ FASE 4: FEATURE ENGINEERING & ML (E7-E8)                            │
├──────────────────────────────────────────────────────────────────────┤
│ 03_feature_engineering.ipynb (Eng. Avançado)       ← Features modelos│
│ Input:  Silver Parquet (s3://...silver/...) OU RDS Gold              │
│ Output: 3 CSVs (série temporal, matriz risco, perfis)               │
│                                                                       │
│ [Notebooks ML] (E8)                                ← Treinar modelos│
│ Input:  CSVs de Gold                                                 │
│ Output: Modelos treinados + Métricas (Prophet, XGBoost, K-Means)    │
└──────────────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────────────┐
│ FASE 5: ORQUESTRAÇÃO & SERVING (E9-E10)                              │
├──────────────────────────────────────────────────────────────────────┤
│ [Airflow DAG] (E9)                                 ← Agendamento    │
│ Executa: 01 → 04 → dbt → 03 → ML (pipeline automático)              │
│                                                                       │
│ [Power BI] (E10)                                   ← Dashboards     │
│ Input:  Modelos (MLflow) + Star Schema (RDS Gold) + Views dbt        │
│ Output: 4 dashboards interativos                                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Matriz de Decisão: Qual Notebook Usar?

| Pergunta | Resposta | Use |
|----------|----------|-----|
| Preciso **carregar XLSX pela primeira vez**? | SIM | 01_pre_processamento_bronze |
| Preciso **entender as distribuições dos dados**? | SIM | 02_eda_silver |
| Preciso **criar Silver (limpar + features)**? | SIM | 04_bronze_silver_transformacao |
| Preciso **criar features para modelos específicos**? | SIM | 03_feature_engineering |
| Preciso **validar dados antes de ML**? | SIM | 02_eda_silver (pós-04) |
| Preciso **agendar tudo automaticamente**? | SIM | Airflow DAG (E9) |

---

## 🔗 Dependências e Ordem de Execução

### Primeira Vez (Setup)
```
1. 01_pre_processamento_bronze.ipynb
   ↓ (gera Bronze: 122.543 registros)
   
2. 02_eda_silver.ipynb (OPCIONAL, para entendimento)
   ↓ (análise exploratória, histogramas, nulos)
   
3. 04_bronze_silver_transformacao.ipynb
   ↓ (gera Silver: 41.441 registros + features)
   
4. 03_dbt_star_schema_ml_marts.ipynb
   ↓ (lê Silver, cria Star Schema no RDS via dbt)
   └─ Resultado: PostgreSQL Gold (dim_*, fact_*, vw_*)
   
5. 03_feature_engineering.ipynb
   ↓ (lê Silver/RDS, cria CSVs específicos para modelos)
   └─ Resultado: df_serie_temporal, df_matriz_risco, df_perfis_cluster
   
6. [ML Notebooks] (04_modelo_forecast, 05_modelo_ola_risk, 06_clusterizacao)
   ↓ (treinar Prophet, XGBoost, K-Means)
   └─ Resultado: Modelos treinados + métricas (MLflow)
```

### Manutenção (Diária/Airflow - E9)
```
Airflow executa sequência automática:

01 (se dados novos) 
  → 04 (Bronze → Silver)
  → [dbt run] (03_dbt_star_schema_ml_marts → RDS Gold)
  → [dbt test] (validações)
  → 03 (Silver → CSVs Gold)
  → [ML predictions] (rodar modelos treinados)
  
Saltam:
  - 02 (apenas mensal para validação)
  - 03_feature_engineering (features criadas uma vez, reutilizadas)
  - Notebooks ML treino (rodam manualmente, E8)
```

---

## ⚙️ Integração com Infraestrutura

### Terraform (IaC)
```
S3 Buckets:
├─ bronze/incidents_standardized.parquet/  (output 01)
├─ silver/incidents_silver_2025.parquet/   (output 04)
└─ gold/df_*.csv                            (output 03)

RDS PostgreSQL:
└─ Public schema (output dbt, E6-E7)
```

### Glue Job (E5)
```
[Futuro] Transform_bronze_to_silver job
├─ Código: pipeline/silver/transform_bronze_to_silver.py
├─ Input: s3://...bronze/...
├─ Output: s3://...silver/...
└─ Trigger: Airflow DAG (E9)
```

---

## 📝 Checklist de Implementação

### Infraestrutura & Data Lake
- [ ] **E4**: 01_pre_processamento_bronze.ipynb criado + testado
- [ ] **E4**: Bronze Parquet gerado em S3 (122.543 registros, 19 cols)
- [ ] **E4**: Partições S3 Bronze criadas (ano/mês)

### Exploração & Transformação
- [ ] **E5**: 02_eda_silver.ipynb criado (análise exploratória, gráficos)
- [ ] **E5**: 04_bronze_silver_transformacao.ipynb criado + testado
- [ ] **E5**: Silver Parquet gerado em S3 (41.441 registros, 25 cols)
- [ ] **E5**: 6 Features derivadas validadas
- [ ] **E5**: Target_Risco_SLA calculado corretamente
- [ ] **E5**: Partições S3 Silver criadas (Ano_Mes)

### Data Warehouse & Analytics
- [ ] **E6-E7**: RDS PostgreSQL configurado (aiops_gold database)
- [ ] **E6-E7**: 03_dbt_star_schema_ml_marts.ipynb criado + testado
- [ ] **E6-E7**: dbt models criados (dim_*, fact_*, vw_*)
- [ ] **E6-E7**: dbt testes (unique, not_null, relationships) passando
- [ ] **E6-E7**: dbt docs gerados (lineage de transformações)
- [ ] **E6-E7**: Star Schema validado no RDS

### Feature Engineering & ML
- [ ] **E7**: 03_feature_engineering.ipynb criado (lê Silver/RDS)
- [ ] **E7**: 3 CSVs Gold gerados (série_temporal, matriz_risco, perfis_cluster)
- [ ] **E8**: ML notebooks criados (04_modelo_forecast, 05_modelo_ola_risk, 06_clusterizacao)
- [ ] **E8**: Modelos treinados + métricas registradas (MLflow)

### Orquestração & Serving
- [ ] **E9**: Airflow DAG criado (aiops_pipeline_dag.py)
- [ ] **E9**: DAG agendado (diariamente) com dependências corretas
- [ ] **E9**: CloudWatch logs configurados (monitoramento)
- [ ] **E10**: Power BI conectado ao RDS Gold
- [ ] **E10**: 4 Dashboards criados (painel_geral, alertas_sla, volume, eficiência)

---

## 📞 Referências Rápidas

| O que? | Onde? |
|--------|-------|
| Bronze standardizado | `s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet/` |
| Silver pronto para ML | `s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet/` |
| Gold features (CSV) | `s3://aiops-locaweb-datalake-2026/gold/df_*.csv` |
| Star Schema (RDS) | PostgreSQL aiops_gold (public schema) |
| Plano técnico (Glue) | `md/PLANO_GLUE_SILVER_PARQUET.md` |
| Setup geral | `CLAUDE.md` |

---

**Documento Preparado**: 2026-05-18  
**Revisor**: Claude Haiku  
**Status**: Pronto para Implementação
