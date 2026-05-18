# 📦 Terraform Modularizado - Guia Rápido

## Estrutura

```
infra/terraform/
├── provider.tf                          # AWS provider config
├── variables.tf                         # Variáveis raiz (aws_region, aws_profile, rds_password)
├── main.tf                              # Orquestração dos módulos (~30 linhas)
├── outputs.tf                           # Agregação de outputs
│
└── modules/
    ├── network/                         # VPC, Subnets, IGW
    │   ├── main.tf
    │   └── outputs.tf
    │
    ├── storage/                         # Bucket S3 Data Lake
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    │
    └── database/                        # RDS PostgreSQL + Glue
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

---

## Comandos Rápidos

### ✅ Setup Inicial (Network + Storage)

```bash
cd infra/terraform
terraform init
terraform validate
terraform plan
terraform apply
```

### 🔌 Ativar RDS + Glue (quando pronto)

1. Descomente o módulo `database` em `main.tf`
2. Execute:

```bash
terraform plan -var="rds_password=SenhaForte123!"
terraform apply -var="rds_password=SenhaForte123!"
```

### 📊 Ver Outputs

```bash
terraform output                    # Todos
terraform output bucket_id          # Específico
terraform output -json              # Formato JSON
```

### 🗑️ Destruir Infraestrutura

```bash
terraform destroy
# Ou apenas descomente o módulo database e aplique
```

---

## Módulos Explicados

| Módulo | Recursos | Variáveis | Dependências | Status |
|--------|----------|-----------|--------------|--------|
| **network** | VPC, 2 Subnets, IGW | Nenhuma | - | ✅ Ativo |
| **storage** | S3 Bucket | `bucket_name` | - | ✅ Ativo |
| **database** | RDS, DB Subnet Group, Glue | `subnet_ids`, `rds_password` | network | 🔴 Comentado |

---

## Vantagens desta Arquitetura

✅ **Legível**: main.tf com apenas 25-30 linhas (vs. 200+ antes)  
✅ **Modular**: Cada módulo tem responsabilidade clara  
✅ **Reutilizável**: Mesmo código para dev, staging, prod  
✅ **Flexível**: Ligar/desligar modules com comentários  
✅ **Escalável**: Fácil adicionar novos módulos  

---

## Variáveis Necessárias

### Ao Aplicar

```bash
terraform apply \
  -var="aws_region=us-east-1" \
  -var="aws_profile=aiops-project" \
  -var="rds_password=SenhaForte123!"  # Apenas se database descomentado
```

Ou criar arquivo `.tfvars`:
```hcl
aws_region     = "us-east-1"
aws_profile    = "aiops-project"
rds_password   = "SenhaForte123!"
```

```bash
terraform apply -var-file="terraform.tfvars"
```

---

## Outputs Principais

```
vpc_id                = "vpc-xxxxx"
subnet_ids            = ["subnet-aaa", "subnet-bbb"]
bucket_id             = "aiops-locaweb-datalake-2026"
bucket_arn            = "arn:aws:s3:::aiops-locaweb-datalake-2026"
```

---

## Troubleshooting

| Problema | Solução |
|----------|---------|
| Bucket já existe | Trocar `bucket_name` em main.tf (S3 é global) |
| VPC cidr duplicado | `terraform refresh` e depois `plan` |
| RDS não cria subnets | Verificar se network foi aplicado antes (dependência) |
| Outputs com erro | Descomente database e tente novamente |

---

## Documentação Completa

Veja `docs/TERRAFORM_MODULARIZADO.md` para detalhes completos, exemplos e boas práticas.
