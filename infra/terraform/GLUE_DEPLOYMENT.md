# Deployment: Glue Job Bronze → Silver (E5)

Este documento explica como fazer deploy do Glue job via Terraform.

---

## 📋 Pré-requisitos

1. **AWS CLI configurado**
   ```bash
   aws configure --profile aiops-project
   aws sts get-caller-identity --profile aiops-project
   ```

2. **Terraform instalado** (v1.0+)
   ```bash
   terraform version
   ```

3. **S3 bucket já criado** (módulo `storage`)
   ```bash
   terraform apply -target=module.storage
   ```

---

## 🚀 Deploy do Glue Job

### Passo 1: Validar Terraform

```bash
cd infra/terraform
terraform validate
```

**Output esperado**:
```
Success! The configuration is valid.
```

### Passo 2: Plan (visualizar o que será criado)

```bash
terraform plan -target=module.glue
```

**Output esperado**:
```
Plan: 7 to add, 0 to change, 0 to destroy.

Resources to add:
  + aws_iam_role.glue_job_role
  + aws_iam_role_policy.glue_s3_policy
  + aws_iam_role_policy_attachment.glue_logs_policy
  + aws_s3_object.glue_script_transform
  + aws_s3_object.glue_module_config
  + aws_s3_object.glue_module_transformations
  + aws_s3_object.glue_module_validators
  + aws_s3_object.glue_module_logger
  + aws_glue_job.transform_bronze_to_silver
```

### Passo 3: Apply (criar o Glue job)

```bash
terraform apply -target=module.glue
```

Digite `yes` quando pedido.

**Output esperado**:
```
Apply complete! Resources: 9 added, 0 changed, 0 destroyed.

Outputs:

glue_job_name = "transform_bronze_to_silver"
glue_job_arn = "arn:aws:glue:us-east-1:XXXX:job/transform_bronze_to_silver"
glue_script_location = "s3://aiops-locaweb-datalake-2026/scripts/transform_bronze_to_silver.py"
```

---

## ▶️ Executar o Glue Job

### Via AWS Console

1. Ir para **AWS Glue** → **Jobs**
2. Selecionar `transform_bronze_to_silver`
3. Clicar **Run job**

### Via AWS CLI

```bash
aws glue start-job-run \
  --job-name transform_bronze_to_silver \
  --profile aiops-project
```

**Output**:
```json
{
  "JobRunId": "jr_123456789abc"
}
```

### Monitorar Execução

```bash
# Visualizar status
aws glue get-job-run \
  --job-name transform_bronze_to_silver \
  --run-id jr_123456789abc \
  --profile aiops-project

# Ver logs em CloudWatch
aws logs tail /aws-glue/transform_bronze_to_silver --follow --profile aiops-project
```

---

## 📊 Validação pós-execução

### 1. Verificar se Parquet foi criado

```bash
aws s3 ls s3://aiops-locaweb-datalake-2026/silver/ \
  --recursive \
  --profile aiops-project
```

**Output esperado**:
```
2026-05-19 14:30:45          0 silver/incidents_silver_2025.parquet/
2026-05-19 14:30:47  12345678 silver/incidents_silver_2025.parquet/part-00000.parquet
2026-05-19 14:30:49  12345678 silver/incidents_silver_2025.parquet/part-00001.parquet
...
2026-05-19 14:31:10       1234 silver/incidents_silver_2025.parquet/_SUCCESS
```

### 2. Carregar Silver para RDS (próximo: load_s3_to_rds.py)

```bash
cd pipeline/silver
python load_s3_to_rds.py
```

---

## ⚙️ Configuração Free Tier

O job está configurado para **ficar dentro do Free Tier**:

```
Cálculo de DPU-minutos por execução:
- Worker Type: G.1X (1 DPU/worker)
- Num Workers: 3
- Timeout: 60 minutos
- Tempo real esperado: 15-25 minutos

DPU-minutos = 3 workers × 20 min (estimado) = 60 DPU-minutos/execução
DPU-minutos/mês = 60 × 20 execuções = 1.200 DPU-min/mês

Free Tier: 6.000 DPU-min/mês
Margem: 4.800 DPU-min (80% disponível) ✅
```

---

## 🔧 Personalizar Configuração

Se precisar ajustar o job (e.g., mais workers, timeout maior):

### Opção 1: Via variáveis

```bash
terraform apply \
  -target=module.glue \
  -var="num_workers=5" \
  -var="timeout_minutes=120"
```

### Opção 2: Editar `modules/glue/variables.tf`

```hcl
variable "num_workers" {
  default = 5  # Aumentar de 3 para 5
}

variable "timeout_minutes" {
  default = 120  # Aumentar de 60 para 120
}
```

**Atenção**: Aumentar workers pode sair do Free Tier!

---

## 🗑️ Destruir o Glue Job

Se precisar remover tudo:

```bash
terraform destroy -target=module.glue
```

Isto irá:
- ✅ Deletar o job Glue
- ✅ Remover scripts do S3
- ✅ Deletar roles/policies IAM
- ❌ **NÃO** deletar o bucket S3

---

## 📌 Próximos Passos

1. ✅ Deploy Glue via Terraform
2. → Executar Glue job (1-2 minutos)
3. → Validar Parquet em S3 (silver/)
4. → Rodar `load_s3_to_rds.py` para carregar RDS
5. → E6: Executar `dbt run` em Silver

---

## 📚 Referências

- [docs/VALIDACAO_FREE_TIER_GLUE.md](../../docs/VALIDACAO_FREE_TIER_GLUE.md)
- [docs/E5_GLUE_SILVER_STATUS.md](../../docs/E5_GLUE_SILVER_STATUS.md)
- [pipeline/silver/README_LOAD_S3_RDS.md](../../pipeline/silver/README_LOAD_S3_RDS.md)
