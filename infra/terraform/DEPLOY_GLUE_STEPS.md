# 🚀 Deploy Glue Job - Passos de Execução

Siga exatamente estes passos **na sua máquina** para fazer deploy do Glue job.

---

## ✅ Passo 1: Inicializar Terraform (uma única vez)

```powershell
cd d:\Projetos\AWS_Portifolio\Projeto aws\infra\terraform
terraform init
```

**Esperado**: Terraform processa módulos e inicializa backend.

```
Initializing modules...
- glue in modules/glue
- storage in modules/storage
- network in modules/network
- database in modules/database

Terraform has been successfully initialized!
```

---

## ✅ Passo 2: Validar Configuração

```powershell
terraform validate
```

**Esperado**:
```
Success! The configuration is valid.
```

---

## ✅ Passo 3: Visualizar o Que Será Criado (Plan)

```powershell
terraform plan -target=module.glue
```

**Esperado**: Mostra 11 recursos a serem criados:
- `aws_iam_role`
- `aws_iam_role_policy`
- `aws_iam_role_policy_attachment`
- `aws_s3_object` (7 arquivos Python)
  - upload_xlsx.py (E4)
  - xlsx_to_parquet.py (E4→E5)
  - transform_bronze_to_silver.py (E5)
  - config.py, transformations.py, validators.py, logger.py (módulos)
- `aws_glue_job`

```
Plan: 11 to add, 0 to change, 0 to destroy.
```

---

## ✅ Passo 4: Deploy (Apply)

```powershell
$env:AWS_PROFILE = "aiops-project"
terraform apply -target=module.glue
```

**Será pedido**: Deseja fazer apply? Digite `yes` e pressione Enter.

**Esperado** (após 2-3 minutos):
```
Apply complete! Resources: 9 added, 0 changed, 0 destroyed.

Outputs:

glue_job_name = "transform_bronze_to_silver"
glue_job_arn = "arn:aws:glue:us-east-1:XXXX:job/transform_bronze_to_silver"
glue_script_location = "s3://aiops-locaweb-datalake-2026/scripts/transform_bronze_to_silver.py"
```

---

## ✅ Passo 5: Verificar Deploy no S3

```powershell
$env:AWS_PROFILE = "aiops-project"
aws s3 ls s3://aiops-locaweb-datalake-2026/scripts/ --recursive
```

**Esperado**: 7 arquivos Python uploadados para S3:
```
upload_xlsx.py                    (E4: Upload XLSX)
xlsx_to_parquet.py                (E4→E5: Converter Parquet)
transform_bronze_to_silver.py     (E5: Glue job principal)
config.py                         (Configurações)
transformations.py                (Funções de transformação)
validators.py                     (Validadores)
logger.py                         (Logger customizado)
```

---

## ✅ Passo 6: Executar o Job Glue

### Opção A: Via AWS Console
1. Acessar https://us-east-1.console.aws.amazon.com/glue/
2. Clicar em **Jobs** no menu esquerdo
3. Selecionar `transform_bronze_to_silver`
4. Clicar **Run job**
5. Acompanhar status em **Runs**

### Opção B: Via CLI (recomendado)

```powershell
$env:AWS_PROFILE = "aiops-project"
aws glue start-job-run --job-name transform_bronze_to_silver
```

**Será retornado**:
```json
{
  "JobRunId": "jr_abc123..."
}
```

---

## ✅ Passo 7: Monitorar Execução

```powershell
$env:AWS_PROFILE = "aiops-project"

# Verificar status (substitua JOB_RUN_ID pelo valor acima)
aws glue get-job-run `
  --job-name transform_bronze_to_silver `
  --run-id jr_abc123...

# Ver logs em CloudWatch
aws logs tail /aws-glue/transform_bronze_to_silver --follow
```

**Esperado**: Status progride de `RUNNING` → `SUCCEEDED` (15-25 min)

---

## ✅ Passo 8: Validar Output Silver

Após job completar com sucesso:

```powershell
$env:AWS_PROFILE = "aiops-project"
aws s3 ls s3://aiops-locaweb-datalake-2026/silver/incidents_silver_2025.parquet/ --recursive
```

**Esperado**: Parquets particionados por mês (Ano_Mes):
```
2026-05-19 14:30:47  12345678 silver/incidents_silver_2025.parquet/Ano_Mes=2025-01/part-00000.parquet
2026-05-19 14:30:47  12345678 silver/incidents_silver_2025.parquet/Ano_Mes=2025-02/part-00000.parquet
...
2026-05-19 14:31:10       1234 silver/incidents_silver_2025.parquet/_SUCCESS
```

---

## 📌 Próximos Passos (E6 - dbt)

Após validar Parquet em S3:

```powershell
# Carregar Silver para RDS
cd d:\Projetos\AWS_Portifolio\Projeto aws\pipeline\silver
python load_s3_to_rds.py

# Executar dbt Silver (E6)
cd dbt\aiops_dbt
dbt run --select silver
dbt test --select silver
```

---

## ⚠️ Troubleshooting

### Erro: "AccessDenied" ao executar apply

```
Verificar:
1. AWS_PROFILE está correto?
   $env:AWS_PROFILE
   
2. Credenciais existem?
   aws sts get-caller-identity --profile aiops-project
```

### Erro: "FileNotFound" ao upload

```
Verificar:
1. Você está no diretório correto?
   pwd  # deve ser infra/terraform
   
2. Arquivos pipeline/silver/ existem?
   ls ..\..\pipeline\silver\*.py
```

### Erro: "Free Tier exceeded"

Ajuste workers em `modules/glue/variables.tf`:
```hcl
variable "num_workers" {
  default = 2  # Reduzir de 3 para 2
}
```

---

## 📊 Checklist de Execução

- [ ] `terraform init` executado
- [ ] `terraform validate` passou
- [ ] `terraform plan -target=module.glue` revisado
- [ ] `terraform apply -target=module.glue` completado
- [ ] Scripts vistos em S3 `/scripts/`
- [ ] Glue job executado e completou com status SUCCEEDED
- [ ] Silver Parquet criado em S3 `/silver/incidents_silver_2025.parquet/`
- [ ] `load_s3_to_rds.py` completado
- [ ] dbt Silver rodado com sucesso (E6)

---

**Status**: ✅ Glue job definido em Terraform  
**Próximo**: Você executa os passos acima na sua máquina
