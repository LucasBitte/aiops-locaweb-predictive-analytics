# Pipeline Silver: Bronze → Silver Transformation

Módulo Apache Glue para transformação da camada Bronze em Silver do Data Lake AIOps Locaweb.

## Visão Geral

```
S3 Bronze (incidents_standardized.parquet - 122.543 registros)
    ↓
[Glue Job: transform_bronze_to_silver.py]
    ├─ Validação de schema
    ├─ Filtragem temporal (2025+)
    ├─ Feature engineering (6 features)
    ├─ Tratamento de nulos
    ├─ Cálculo de targets (risco SLA)
    └─ Persistência em Parquet particionado
    ↓
S3 Silver (incidents_silver_2025.parquet - 41.441 registros)
```

## Stack

- **Apache Glue 4.0+** com PySpark 3.3+
- **Python 3.9+**
- **AWS S3** para storage
- **CloudWatch** para logging

## Estrutura de Arquivos

```
pipeline/silver/
├── __init__.py                      # Módulo package
├── config.py                        # Configurações globais (caminhos, limites)
├── transformations.py               # Feature engineering e targets (reutilizável)
├── validators.py                    # Validações de schema e qualidade
├── logger.py                        # Logging centralizado (CloudWatch)
├── transform_bronze_to_silver.py    # Job Glue principal
├── test_transformations.py          # Testes unitários (pytest)
└── README.md                        # Este arquivo
```

## Como Usar

### 1. Localmente (Testes)

```bash
# Instalar dependências
pip install pyspark pytest

# Rodar testes unitários
pytest pipeline/silver/test_transformations.py -v

# Rodar teste específico
pytest pipeline/silver/test_transformations.py::TestFeatureExigeIntervencao -v
```

### 2. Em Glue Job (Production)

#### 2.1 Upload de Scripts para S3

```bash
# Criar pasta de scripts em S3
aws s3 mkdir s3://aiops-locaweb-datalake-2026/scripts/glue/

# Upload de todos os módulos
aws s3 cp pipeline/silver/*.py s3://aiops-locaweb-datalake-2026/scripts/glue/ --recursive
```

#### 2.2 Criar Job Glue via Terraform

```bash
cd infra/terraform
terraform apply -target=aws_glue_job.transform_bronze_to_silver
```

#### 2.3 Executar Job (Manual)

```bash
# Executar via console AWS ou:
aws glue start-job-run \
  --job-name transform_bronze_to_silver \
  --worker-type G.2X \
  --number-of-workers 10
```

#### 2.4 Monitorar Execução

```bash
# Ver logs em CloudWatch
aws logs tail /aws/glue/transform_bronze_to_silver --follow

# Ou no console AWS:
# CloudWatch → Log Groups → /aws/glue/transform_bronze_to_silver
```

## Módulos

### config.py

Define constantes globais:
- **BRONZE_PATH**: Localização input
- **SILVER_PATH**: Localização output
- **MIN_DATE**: Data mínima de filtro
- **EXPECTED_SCHEMA_COLS**: Schema esperado do Bronze
- **FILLNA_RULES**: Regras de preenchimento de nulos
- **Limites de validação**: min_records, max_null_ratio, etc.

### transformations.py

6 **funções reutilizáveis** de feature engineering:

| Feature | Descrição | Tipo | Valores |
|---------|-----------|------|--------|
| `Exige_Intervencao` | Esforço real vs. ruído | Bool (0/1) | Status != 'Sem Intervenção' |
| `Prioridade_Num` | Extrai número de P1-P5 | Int (1-5) | Substring de Prioridade |
| `Possui_Pai` | Incidente vinculado | Bool (0/1) | NOT NULL Incidente_Pai |
| `Duracao_Horas` | Duração em horas | Float | Duração / 3600 |
| `Data_Abertura` | Data sem hora | Date | CAST(Aberto AS DATE) |
| `Ano_Mes` | Partição (yyyy-MM) | String | DATE_FORMAT(Aberto, 'yyyy-MM') |
| `KPI_Status_Int` | KPI normalizado | Int (-1/0/1) | SIM→1, NAO→0, NULL→-1 |

### Target: `Target_Risco_SLA` (3 camadas)

```
Layer 1 (Base): KPI_Status_Int = 1 → Violado
Layer 2 (Heurística): P2 + duração > 4h + KPI desconhecido → força violação
Layer 3 (Isenção): Possui_Pai=1 OU Exige_Intervencao=0 → sempre OK
```

### validators.py

Validações em 4 pontos:

1. **validate_schema()**: Colunas esperadas existem?
2. **validate_not_empty()**: DataFrame possui registros?
3. **validate_critical_nulls()**: Nulos em colunas críticas?
4. **validate_silver_output()**: Qualidade geral (registros, distribuições)?

### logger.py

Logger centralizado que escreve em:
- **stdout** (exibido no Glue Job console)
- **CloudWatch** (persistido para análise)

Métodos:
- `log.info(msg)` - Informação
- `log.error(msg)` - Erro
- `log.warning(msg)` - Aviso
- `log.section(title)` - Seção com separadores
- `log.dataframe_info(name, df)` - Log de DataFrame
- `log.dict_stats(dict)` - Log de JSON formatado
- `log.job_summary(input, output, duration)` - Resumo final

### transform_bronze_to_silver.py

Job Glue principal com pipeline:

```python
1. read_bronze()          # Lê S3 Bronze
2. validate_schema()      # Valida estrutura
3. filter_temporal()      # Filtra 2025+
4. create_features()      # 6 features
5. sanitize_nulls()       # Nulos → valores padrão
6. compute_targets()      # 3 camadas de risco
7. write_silver()         # Escreve S3 Silver (particionado)
8. generate_quality_report() # Estatísticas + validações
```

## Inputs e Outputs

### Input

**Localização**: `s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet`

| Métrica | Valor |
|---------|-------|
| Registros | 122.543 |
| Colunas | 19 |
| Formato | Parquet |
| Particionamento | Por ano/mês (Bronze) |

### Output

**Localização**: `s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet`

| Métrica | Valor |
|---------|-------|
| Registros | 41.441 |
| Colunas | 25 (19 orig + 6 features) |
| Formato | Parquet |
| **Particionamento** | **Ano_Mes** (2025-01 → 2025-12) |

### Exemplo: Estrutura S3 Silver

```
s3://aiops-locaweb-datalake-2026/silver/
├── Ano_Mes=2025-01/
│   ├── part-00000.parquet
│   ├── part-00001.parquet
│   └── ...
├── Ano_Mes=2025-02/
│   ├── part-00000.parquet
│   └── ...
└── ...
└── Ano_Mes=2025-12/
```

## Estatísticas Esperadas

Após transformação Bronze → Silver (2025):

| Métrica | Valor |
|---------|-------|
| Total de registros | 41.441 |
| Com esforço real | ~41.240 (99.5%) |
| Sem intervenção (ruído) | ~201 (0.5%) |
| Violações de SLA | ~580 (1.4% do esforço) |
| Sem violações | ~40.660 (98.6%) |

**Nota**: Desequilíbrio de classes (1.4% violado) é **desejável** para modelos de risco.

## Validações

### Durante Execução

- ✅ Schema Bronze contém colunas esperadas
- ✅ Não há registros duplos em Número
- ✅ Datas estão no formato esperado
- ✅ Prioridade contém P1-P5
- ✅ Nulos críticos foram preenchidos

### Pós-Escrita

- ✅ Parquet escrito com sucesso
- ✅ Partições criadas (12 meses de 2025)
- ✅ Cada partição contém ~3.450 registros
- ✅ Target_Risco_SLA contém apenas 0/1
- ✅ Nenhuma coluna crítica com nulos

## CloudWatch Logs

### Grupo de Logs

```
/aws/glue/transform_bronze_to_silver
```

### Exemplo de Log Sucesso

```
[2026-05-18T14:30:00] [INFO] ============================================================
[2026-05-18T14:30:00] [INFO] INICIANDO JOB: transform_bronze_to_silver
[2026-05-18T14:30:00] [INFO] ============================================================
[2026-05-18T14:30:05] [INFO] ✅ Bronze carregado: 122.543 registros
[2026-05-18T14:30:10] [INFO] ✅ Schema validado
[2026-05-18T14:30:15] [INFO] ✅ Registros filtrados: 122.543 → 41.441
[2026-05-18T14:30:20] [INFO] ✅ 6 features derivadas criadas
[2026-05-18T14:30:25] [INFO] ✅ Nulos tratados
[2026-05-18T14:30:30] [INFO] ✅ Target_Risco_SLA calculado
[2026-05-18T14:35:00] [INFO] ✅ Silver persistido: 41.441 registros
[2026-05-18T14:35:05] [INFO] ✅ JOB CONCLUÍDO COM SUCESSO
```

## Troubleshooting

### Job Timeout (> 60 min)

**Causa**: Número de workers insuficiente

**Solução**:
```bash
# Aumentar workers de 10 para 20 em config.py
GLUE_NUM_WORKERS = 20
```

### Parquet Corrupted

**Causa**: Job interrompido ou erro de escrita

**Solução**:
```bash
# Limpar S3 Silver
aws s3 rm s3://aiops-locaweb-datalake-2026/silver/ --recursive

# Re-rodar job
aws glue start-job-run --job-name transform_bronze_to_silver
```

### Muitos Nulos em Output

**Causa**: Regra de preenchimento ausente em config.FILLNA_RULES

**Solução**:
1. Adicionar regra em `config.py`
2. Re-rodar job

### Target com Valores > 1

**Causa**: Lógica de 3 camadas não aplicada corretamente

**Solução**:
```python
# Verificar em transformations.py → calculate_target_risco_sla()
# Target deve ser sempre 0 ou 1
```

## Próximos Passos

- **E6**: Usar Silver Parquet como source de dbt models
- **E7**: Criar star schema e features ML no RDS via dbt
- **E8**: Treinar modelos (Prophet, XGBoost, K-Means)
- **E9**: Integrar com Airflow DAG

## Referências

- [PLANO_GLUE_SILVER_PARQUET.md](../../md/PLANO_GLUE_SILVER_PARQUET.md) - Plano detalhado
- [CLAUDE.md](../../CLAUDE.md) - Setup geral do projeto
- [AWS Glue Docs](https://docs.aws.amazon.com/glue/) - Documentação oficial

---

**Épico**: E5 - Analytics Exploratória  
**Versão**: 1.0  
**Data**: 2026-05-18  
**Autor**: Lucas Bittencourt
