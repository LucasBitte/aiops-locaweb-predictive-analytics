# Bronze Layer: XLSX → Parquet

**Épico**: E4 (Ingestão) → E5 (EDA + Glue Silver)

**Objetivo**: Converter dados brutos ITSM (Excel) em formato otimizado (Parquet) para Glue processar.

---

## 📊 Fluxo

```
data/raw/LW-DATASET.xlsx (local)
         ↓
  [upload_xlsx.py]
         ↓
s3://bucket/bronze/LW-DATASET.xlsx (Excel no S3)
         ↓
  [xlsx_to_parquet.py]
         ↓
s3://bucket/bronze/incidents_standardized.parquet (Parquet)
         ↓
  [Glue Job: transform_bronze_to_silver]
         ↓
s3://bucket/silver/incidents_silver_2025.parquet/
```

---

## 🚀 Passo 1: Upload XLSX (E4)

Se ainda não fez, faça upload do arquivo Excel para S3:

```bash
cd pipeline/bronze
python upload_xlsx.py
```

**Pré-requisitos**:
- Arquivo `data/raw/LW-DATASET.xlsx` existe localmente
- AWS credentials configuradas (`AWS_PROFILE`)

**Output esperado**:
```
[2026-05-19 10:00:00] INFO: ⏳ Iniciando upload de data/raw/LW-DATASET.xlsx...
[2026-05-19 10:00:05] INFO: ✅ Sucesso! Arquivo disponível em: s3://aiops-locaweb-datalake-2026/bronze/LW-DATASET.xlsx
[2026-05-19 10:00:05] INFO: 📊 Validação inicial: 122000 registros detectados no arquivo local.
```

---

## 🔄 Passo 2: Converter XLSX → Parquet (E4→E5)

Agora converta o Excel para Parquet:

```bash
cd pipeline/bronze
python xlsx_to_parquet.py
```

**O que faz**:
1. ✅ Lê `LW-DATASET.xlsx` do S3
2. ✅ Valida schema (17 colunas esperadas)
3. ✅ Converte tipos de dados (datas, números, strings, booleanos)
4. ✅ Salva como Parquet comprimido
5. ✅ Gera estatísticas

**Output esperado**:
```
======================================================================
BRONZE: XLSX → Parquet Conversion (E4→E5)
======================================================================

[2026-05-19 10:05:00] INFO: Iniciando conversão...
[2026-05-19 10:05:00] INFO: Lendo XLSX do S3: s3://aiops-locaweb-datalake-2026/bronze/LW-DATASET.xlsx...
[2026-05-19 10:05:05] INFO: ✅ Carregado do S3: 122000 registros
[2026-05-19 10:05:05] INFO: Validando schema (17 colunas esperadas)...
[2026-05-19 10:05:05] INFO: ✅ Schema válido
[2026-05-19 10:05:05] INFO: Convertendo tipos de dados...
[2026-05-19 10:05:06] INFO: ✅ Tipos de dados convertidos
[2026-05-19 10:05:06] INFO: Gerando estatísticas...

📊 Estatísticas do Dataset:
   - Registros: 122,000
   - Colunas: 17
   - Período: 2024-06-01 → 2025-12-31
   - Memória (MB): 45.32

[2026-05-19 10:05:07] INFO: Salvando em Parquet...
[2026-05-19 10:05:10] INFO: Convertendo para Parquet...
[2026-05-19 10:05:12] INFO: Fazendo upload para s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet...
[2026-05-19 10:05:15] INFO: ✅ Parquet salvo em S3

======================================================================
✅ CONVERSÃO CONCLUÍDA COM SUCESSO
======================================================================

Proximos passos:
1. Glue job pode consumir: s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet
2. Executar Glue: transform_bronze_to_silver
3. Validar Silver em S3: s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet/
```

---

## ✅ Passo 3: Validar Parquet em S3

Depois da conversão, verifique se o arquivo foi criado:

```bash
$env:AWS_PROFILE = "aiops-project"
aws s3 ls s3://aiops-locaweb-datalake-2026/bronze/ --recursive
```

**Output esperado**:
```
2026-05-19 10:00:05  45321234 bronze/LW-DATASET.xlsx
2026-05-19 10:05:15  38214567 bronze/incidents_standardized.parquet
```

---

## 🔧 Configuração

### Via Variáveis de Ambiente

Editar `.env`:
```bash
S3_BUCKET=aiops-locaweb-datalake-2026
AWS_PROFILE=aiops-project
```

### Diretamente no Script

Se preferir, edite as constantes no topo de `xlsx_to_parquet.py`:
```python
S3_BUCKET = "aiops-locaweb-datalake-2026"
XLSX_PATH = "s3://aiops-locaweb-datalake-2026/bronze/LW-DATASET.xlsx"
PARQUET_PATH = "s3://aiops-locaweb-datalake-2026/bronze/incidents_standardized.parquet"
```

---

## 🐛 Troubleshooting

### Erro: "No such file or directory: data/raw/LW-DATASET.xlsx"

Certifique-se que o arquivo está em:
```bash
ls data/raw/LW-DATASET.xlsx
```

Se não existe, adicione o arquivo lá ou ajuste o caminho no script.

### Erro: "AccessDenied" ao fazer upload

Verificar credenciais AWS:
```bash
aws sts get-caller-identity --profile aiops-project
```

Se falhar, reconfigure:
```bash
aws configure --profile aiops-project
```

### Erro: "Schema inválido. Colunas faltando: {...}"

O arquivo Excel não tem todas as 17 colunas esperadas. Verifique a estrutura:

```python
EXPECTED_COLS = [
    'Número', 'Prioridade', 'Produto', 'Categoria', 'Subcategoria',
    'Grupo_designado', 'Aberto', 'Resolvido', 'Encerrado', 'Duração',
    'Status', 'Entrou_para_KPI', 'KPI_Violado', 'Incidente_Pai',
    'Código_de_fechamento', 'Solução', 'Aberto_por', 'Descrição_resumida'
]
```

---

## 📌 Dependências

```bash
pip install -r requirements.txt
```

Ou manualmente:
```bash
pip install pandas openpyxl pyarrow boto3 python-dotenv
```

---

## 📚 Próximos Passos

1. ✅ `upload_xlsx.py` — XLSX → S3
2. ✅ `xlsx_to_parquet.py` — S3 Parquet criado
3. → **Glue job** (`transform_bronze_to_silver`) — Silver criado
4. → dbt Silver (E6)

---

## 📊 Estrutura de Arquivos

```
pipeline/bronze/
├── upload_xlsx.py              ← E4: Upload XLSX to S3
├── xlsx_to_parquet.py          ← E5: Convert to Parquet
├── README.md                   ← This file
└── [output no S3]
    ├── bronze/LW-DATASET.xlsx
    └── bronze/incidents_standardized.parquet
```

---

**Status**: ✅ Scripts prontos para usar  
**Próximo**: Executar os passos acima sequencialmente
