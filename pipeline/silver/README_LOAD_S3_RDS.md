# Load S3 Silver → RDS PostgreSQL

**Objetivo**: Importar Parquet do S3 (saída Glue) → Tabela RDS (entrada dbt)

**Responsável por**: Conectar camada Lake (S3) com camada Warehouse (RDS)

**Épico**: E5 (ponte Silver)

---

## Fluxo

```
┌─────────────────────────────────────────┐
│ Glue Job (transform_bronze_to_silver.py) │
│ INPUT:  s3://bronze/...parquet          │
│ OUTPUT: s3://silver/incidents_silver_... │
└──────────────┬──────────────────────────┘
               │
               ↓
        (Parquet particionado)
               │
               ↓
┌──────────────────────────────────────────┐
│ Este script: load_s3_to_rds.py           │
│ INPUT:  s3://silver/incidents_silver_... │
│ OUTPUT: RDS raw_incidents_silver         │
└──────────────┬──────────────────────────┘
               │
               ↓
┌──────────────────────────────────────────┐
│ dbt (E6-E7)                              │
│ INPUT:  RDS raw_incidents_silver         │
│ OUTPUT: RDS gold/* (dims + fatos)        │
└──────────────────────────────────────────┘
```

---

## Pré-requisitos

1. **Glue job completou** (S3 Parquet foi gerado)
2. **RDS PostgreSQL criado** com database `aiops` e schema `dbt_dev`
3. **Credenciais AWS configuradas**
   ```bash
   export AWS_ACCESS_KEY_ID=...
   export AWS_SECRET_ACCESS_KEY=...
   ```
4. **Python 3.8+** com dependências
   ```bash
   pip install -r requirements-silver.txt
   ```

---

## Instalação de Dependências

```bash
cd pipeline/silver

# Option 1: usar requirements
pip install -r requirements-silver.txt

# Option 2: manual
pip install pyspark sqlalchemy psycopg2-binary pandas boto3
```

---

## Configuração

### Via Variáveis de Ambiente

```bash
# S3
export S3_SILVER_PATH="s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet/"

# RDS
export RDS_HOST="aiops-db.c9akciq32.us-east-1.rds.amazonaws.com"
export RDS_PORT=5432
export RDS_USER="admin"
export RDS_PASSWORD="SenhaForte123!"
export RDS_DATABASE="aiops"
export RDS_SCHEMA="dbt_dev"

# AWS (se não estiver em AWS credentials)
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

### Via .env (alternativo)

Criar arquivo `.env`:
```
S3_SILVER_PATH=s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet/
RDS_HOST=aiops-db.c9akciq32.us-east-1.rds.amazonaws.com
RDS_PORT=5432
RDS_USER=admin
RDS_PASSWORD=SenhaForte123!
RDS_DATABASE=aiops
RDS_SCHEMA=dbt_dev
```

Depois carregar:
```bash
set -a
source .env
set +a
```

---

## Uso

### Modo 1: Rodar Script Local

```bash
cd pipeline/silver
python load_s3_to_rds.py
```

**Output esperado**:
```
[2026-05-18 14:30:15] INFO: 🚀 Iniciando carga Silver S3 → RDS
[2026-05-18 14:30:15] INFO:    S3 Input:  s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet/
[2026-05-18 14:30:15] INFO:    RDS Output: dbt_dev.raw_incidents_silver
[2026-05-18 14:30:18] INFO: Lendo Silver de s3://...
[2026-05-18 14:30:22] INFO: ✅ Parquet carregado: 41.441 registros, 25 colunas
[2026-05-18 14:30:23] INFO: ✅ Conexão RDS validada
[2026-05-18 14:30:24] INFO: ✅ Tabela dbt_dev.raw_incidents_silver pronta
[2026-05-18 14:30:24] INFO: Limpando tabela dbt_dev.raw_incidents_silver...
[2026-05-18 14:30:25] INFO: ✅ Tabela dbt_dev.raw_incidents_silver truncada
[2026-05-18 14:30:25] INFO: Carregando DataFrame para RDS (41.441 registros)...
[2026-05-18 14:31:35] INFO: ✅ 41.441 registros carregados com sucesso
[2026-05-18 14:31:36] INFO: Criando índices em dbt_dev.raw_incidents_silver...
[2026-05-18 14:31:37] INFO: ✅ Índices criados
[2026-05-18 14:31:38] INFO: Validando carga em dbt_dev.raw_incidents_silver...
[2026-05-18 14:31:39] INFO: ✅ Validação OK: 41.441 registros carregados
[2026-05-18 14:31:40] INFO: ======================================================================
[2026-05-18 14:31:40] INFO: RESUMO DA CARGA - dbt_dev.raw_incidents_silver
[2026-05-18 14:31:40] INFO: ======================================================================
[2026-05-18 14:31:40] INFO: Total de registros: 41.441
[2026-05-18 14:31:40] INFO: Distribuição por período:
[2026-05-18 14:31:40] INFO:   2025-01: 3.245
[2026-05-18 14:31:40] INFO:   2025-02: 3.521
[2026-05-18 14:31:40] INFO:   2025-03: 3.678
[2026-05-18 14:31:40] INFO: ...
[2026-05-18 14:31:40] INFO: Período: 2025-01-01 → 2025-12-31
[2026-05-18 14:31:40] INFO: Validação nulos: Número=0, Data_Abertura=0
[2026-05-18 14:31:40] INFO: ======================================================================
[2026-05-18 14:31:40] INFO: ✅ Carga concluída com sucesso!
```

### Modo 2: Executar via Airflow (E9)

```python
# airflow/dags/aiops_pipeline_dag.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

import sys
sys.path.insert(0, '/path/to/pipeline/silver')
from load_s3_to_rds import main

default_args = {
    'owner': 'aiops',
    'start_date': datetime(2026, 5, 18),
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'aiops_pipeline',
    default_args=default_args,
    schedule_interval='0 1 * * *',  # 01:00 UTC diariamente
)

load_silver = PythonOperator(
    task_id='load_s3_to_rds',
    python_callable=main,
    dag=dag,
)

# ... dbt_run, dbt_test, etc
```

### Modo 3: Executar via Glue Job (melhor para AWS)

Adicionar passo ao Glue job existente:

```python
# No final de transform_bronze_to_silver.py

import subprocess
import sys

def load_to_rds():
    """Chama script de carga após Glue processing."""
    try:
        # Copiar para Glue container (se necessário)
        result = subprocess.run(
            [sys.executable, 's3://scripts/load_s3_to_rds.py'],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            log.info("✅ Carga S3 → RDS concluída")
        else:
            log.error(f"❌ Erro na carga: {result.stderr}")
            raise Exception(result.stderr)
            
    except Exception as e:
        log.error(f"❌ Erro ao carregar RDS: {e}")
        raise

# No final do main()
load_to_rds()
```

---

## Monitoramento

### Verificar se carga foi bem-sucedida

```bash
# Via SQL direto no RDS
psql -h aiops-db.c9akciq32.us-east-1.rds.amazonaws.com \
     -U admin \
     -d aiops \
     -c "SELECT COUNT(*) FROM dbt_dev.raw_incidents_silver;"

# Via Python
python -c "
import psycopg2
conn = psycopg2.connect(
    host='aiops-db.c9akciq32.us-east-1.rds.amazonaws.com',
    port=5432,
    user='admin',
    password='SenhaForte123',
    database='aiops'
)
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM dbt_dev.raw_incidents_silver;')
count = cur.fetchone()[0]
print(f'✅ Registros no RDS: {count:,}')
cur.close()
conn.close()
"
```

### Logs do Glue (se rodar lá)

```bash
aws logs tail /aws/glue/transform_bronze_to_silver --follow
```

### Verificar índices criados

```bash
psql -h aiops-db.c9akciq32.us-east-1.rds.amazonaws.com \
     -U admin \
     -d aiops \
     -c "\d dbt_dev.raw_incidents_silver"
```

---

## Troubleshooting

### Erro: "S3 path does not exist"

```
Verificar:
1. S3_SILVER_PATH está correto?
2. Glue job completou com sucesso?
3. Arquivo Parquet existe em S3?

aws s3 ls s3://aiops-locaweb-datalake-2026/silver/
```

### Erro: "Connection refused" (RDS)

```
Verificar:
1. RDS_HOST está correto?
2. RDS está em running status?
   aws rds describe-db-instances --db-instance-identifier aiops-db

3. Security group libera port 5432?
   aws ec2 describe-security-groups --filters Name=group-name,Values=aiops-sg
```

### Erro: "Database does not exist"

```
Solução:
1. Criar database no RDS:
   psql -U admin -d postgres
   CREATE DATABASE aiops;
   CREATE SCHEMA dbt_dev AUTHORIZATION admin;
```

### Erro: "Permissão negada"

```
Verificar credenciais AWS:
export AWS_PROFILE=aiops-project
aws sts get-caller-identity

Se não conseguir acessar S3:
aws s3 ls s3://aiops-locaweb-datalake-2026/ --profile aiops-project
```

### Erro: "Memory error"

```
Aumentar Spark memory:
python load_s3_to_rds.py --executor-memory 4g
```

---

## Performance

| Métrica | Esperado |
|---------|----------|
| Tempo leitura S3 | 5-10s |
| Tempo conexão RDS | 2-5s |
| Tempo carga 41.4k registros | 30-60s |
| Tempo criação índices | 10-20s |
| **Tempo total** | **1-2 minutos** |

---

## Próximas Etapas

1. ✅ Script cria tabela RDS automaticamente
2. ✅ Script importa dados com validação
3. ✅ Script cria índices para performance
4. → Executar `dbt run` (lê raw_incidents_silver)
5. → Executar `dbt test`
6. → Power BI conecta ao RDS Gold

---

## Referências

- [docs/ARQUITETURA_S3_RDS_BI_ML.md](ARQUITETURA_S3_RDS_BI_ML.md) — Arquitetura completa
- [docs/SETUP_RDS_PARA_DBT.md](SETUP_RDS_PARA_DBT.md) — Setup RDS
- [pipeline/silver/config.py](config.py) — Configurações Glue
- [pipeline/silver/transform_bronze_to_silver.py](transform_bronze_to_silver.py) — Job Glue

---

**Status**: ✅ Script pronto para uso  
**Próximo**: Validar Glue output → Rodar load_s3_to_rds.py → dbt run
