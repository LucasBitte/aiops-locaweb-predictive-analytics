# Deploy Glue Job via boto3

Script Python para fazer deploy do Glue job sem usar Terraform (evita problemas de permissão IAM).

---

## 🚀 Uso

### Passo 1: Configurar variáveis de ambiente

```bash
# Verificar .env ou definir manualmente
$env:AWS_PROFILE = "aiops-deployer"
$env:AWS_REGION = "us-east-1"
$env:S3_BUCKET = "aiops-locaweb-datalake-2026"

# Opcional: se você tiver uma role Glue existente
$env:GLUE_ROLE_ARN = "arn:aws:iam::206226812451:role/SEU_ROLE"
```

### Passo 2: Executar script

```powershell
cd infra\scripts
python deploy_glue_job.py
```

### Output esperado

```
======================================================================
  DEPLOY GLUE JOB (E5) - VIA BOTO3
======================================================================

[2026-05-19 15:00:00] ✅ Conectado como: arn:aws:iam::206226812451:user/aiops-deployer

======================================================================
  FAZENDO UPLOAD DOS SCRIPTS
======================================================================

[2026-05-19 15:00:01] ✅ Uploadando pipeline/bronze/upload_xlsx.py → s3://aiops-locaweb-datalake-2026/scripts/upload_xlsx.py
[2026-05-19 15:00:02] ✅ Uploadando pipeline/bronze/xlsx_to_parquet.py → s3://aiops-locaweb-datalake-2026/scripts/xlsx_to_parquet.py
...
[2026-05-19 15:00:10] ✅ 7 scripts uploadados para S3

======================================================================
  CRIANDO/ATUALIZANDO GLUE JOB
======================================================================

[2026-05-19 15:00:11] ✅ Job criado: transform_bronze_to_silver

======================================================================
  EXECUTANDO GLUE JOB
======================================================================

[2026-05-19 15:00:12] ✅ Job executado: jr_abc123def456

======================================================================
✅ DEPLOYMENT CONCLUÍDO COM SUCESSO
======================================================================

Proximos passos:
1. Monitorar execução do Glue (15-25 min)
2. Validar Silver em S3: s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet/
3. Executar: python pipeline/silver/load_s3_to_rds.py
4. Rodar dbt (E6)
```

---

## ✅ O que o script faz

1. ✅ **Upload 7 scripts** para S3 (`/scripts/`)
2. ✅ **Cria/obtém role IAM** (com todas as permissions necessárias)
3. ✅ **Cria ou atualiza** o Glue job
4. ✅ **Executa** o job (começa a transformação)

---

## 🔧 Configuração via .env

Se preferir, edite `.env` na raiz do projeto:

```
AWS_PROFILE=aiops-deployer
AWS_REGION=us-east-1
S3_BUCKET=aiops-locaweb-datalake-2026
GLUE_ROLE_ARN=  # Deixar vazio para criar automaticamente
```

---

## 📊 Monitorar Execução

Após o script terminar, use estes comandos para acompanhar:

```powershell
$env:AWS_PROFILE = "aiops-deployer"

# Ver status da execução
aws glue get-job-run `
  --job-name transform_bronze_to_silver `
  --run-id jr_abc123def456

# Ver logs em CloudWatch
aws logs tail /aws-glue/transform_bronze_to_silver --follow
```

---

## 🐛 Troubleshooting

### Erro: "AccessDenied" ao fazer upload

```
Verificar credenciais:
$env:AWS_PROFILE = "aiops-deployer"
aws sts get-caller-identity
```

### Erro: "Arquivo não encontrado"

```
Verificar que você está na raiz do projeto:
cd d:\Projetos\AWS_Portifolio\Projeto aws
pwd
```

### Erro: "Role não tem permissão de S3"

O script cria a role com permissões S3 automaticamente. Se falhar:

```powershell
# Passar uma role existente
$env:GLUE_ROLE_ARN = "arn:aws:iam::206226812451:role/ROLE_EXISTENTE"
python deploy_glue_job.py
```

---

## 📚 Próximos Passos

1. ✅ Script completa (7 scripts em S3 + Glue job criado + job executado)
2. → Aguardar 15-25 minutos para job completar
3. → Validar Parquet criado: `aws s3 ls s3://aiops-locaweb-datalake-2026/silver/`
4. → Executar `python pipeline/silver/load_s3_to_rds.py`
5. → Rodar dbt (E6)

---

**Status**: ✅ Script pronto  
**Vantagem**: Sem problemas de IAM, sem Terraform
