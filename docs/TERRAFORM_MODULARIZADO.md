# Terraform Modularizado - AIOps Locaweb

## Visão Geral

A infraestrutura do projeto foi refatorada para seguir as **melhores práticas de mercado**, utilizando **módulos Terraform reutilizáveis e desacoplados**. Isso permite:

- ✅ **Reutilização**: Mesmos módulos para dev, staging, prod com variáveis diferentes
- ✅ **Controle de Custos**: Descomentar apenas módulos necessários
- ✅ **Manutenibilidade**: Código organizado, fácil de ler e evoluir
- ✅ **Escalabilidade**: Adicionar novos ambientes sem duplicação

---

## Estrutura de Pastas

```
infra/terraform/
├── provider.tf              # Configuração AWS (region, profile)
├── variables.tf             # Variáveis de entrada (rds_password, aws_region, aws_profile)
├── main.tf                  # Orquestração: chamadas dos módulos (15 linhas)
├── outputs.tf               # Agregação de outputs dos módulos
│
└── modules/
    ├── network/             # Módulo 1: VPC, Subnets, IGW
    │   ├── main.tf
    │   └── outputs.tf
    │
    ├── storage/             # Módulo 2: S3 Data Lake
    │   ├── main.tf
    │   ├── variables.tf     # bucket_name
    │   └── outputs.tf
    │
    └── database/            # Módulo 3: RDS PostgreSQL + Glue
        ├── main.tf
        ├── variables.tf     # subnet_ids, rds_password
        └── outputs.tf       # rds_endpoint, glue_catalog_database
```

---

## Módulos em Detalhes

### 1. **Módulo `network`**

**Responsabilidade**: Rede VPC, subnets e internet gateway.

**Recursos**:
- `aws_vpc`: VPC principal (10.0.0.0/16)
- `aws_subnet.public_a`: Subnet A (10.0.1.0/24) em us-east-1a
- `aws_subnet.public_b`: Subnet B (10.0.2.0/24) em us-east-1b
- `aws_internet_gateway`: Gateway para acesso público

**Outputs**:
- `vpc_id`: ID da VPC
- `subnet_ids`: Lista com IDs das duas subnets

**Sem dependências** ✅

---

### 2. **Módulo `storage`**

**Responsabilidade**: Bucket S3 para o Data Lake.

**Variáveis**:
```hcl
variable "bucket_name" {
  type = string
}
```

**Recursos**:
- `aws_s3_bucket`: Bucket com versionamento e segurança

**Outputs**:
- `bucket_id`: Nome do bucket
- `bucket_arn`: ARN do bucket

**Sem dependências** ✅

---

### 3. **Módulo `database`**

**Responsabilidade**: RDS PostgreSQL + AWS Glue Catalog.

**Variáveis**:
```hcl
variable "subnet_ids" {
  type = list(string)
}

variable "rds_password" {
  type      = string
  sensitive = true
}
```

**Recursos**:
- `aws_db_subnet_group`: Subnet group para o RDS
- `aws_db_instance`: RDS PostgreSQL 16.1 (db.t3.micro)
- `aws_glue_catalog_database`: Database para o Glue Catalog

**Outputs**:
- `rds_endpoint`: Endpoint para conexão
- `rds_database_name`: Nome do banco (aiops_gold)
- `rds_username`: Usuário padrão (postgres)
- `glue_catalog_database`: Nome da database do Glue

**Depende de**: `network.subnet_ids` ⚠️

---

## Fluxo de Execução (main.tf raiz)

```hcl
module "network" {
  source = "./modules/network"
}

module "storage" {
  source      = "./modules/storage"
  bucket_name = "aiops-locaweb-datalake-2026"
}

# Descomente quando pronto para usar RDS
/*
module "database" {
  source       = "./modules/database"
  subnet_ids   = module.network.subnet_ids    # Dependência explícita
  rds_password = var.rds_password
}
*/
```

### Por que comentado?

**RDS gera custos** após 12 meses de Free Tier. Mantemos:
- Network (VPC, Subnets) → Sem custo no Free Tier ✅
- Storage (S3) → Sem custo no Free Tier ✅
- Database (RDS) → Custo → Descomente apenas quando usar

---

## Como Usar

### 1️⃣ Setup Inicial

```bash
cd infra/terraform

# Inicializar Terraform (faz download de módulos e plugins)
terraform init

# Validar sintaxe
terraform validate

# Ver o que será criado (só Network + Storage)
terraform plan
```

### 2️⃣ Aplicar (criar Network + S3)

```bash
terraform apply

# Output esperado:
# ✅ aws_vpc.main (criada)
# ✅ aws_subnet.public_a (criada)
# ✅ aws_subnet.public_b (criada)
# ✅ aws_internet_gateway.igw (criada)
# ✅ aws_s3_bucket.datalake (criada)
```

### 3️⃣ Descomente Database (quando pronto)

No `main.tf`, descomente o módulo database:

```hcl
module "database" {
  source       = "./modules/database"
  subnet_ids   = module.network.subnet_ids
  rds_password = var.rds_password
}
```

### 4️⃣ Aplicar com RDS

```bash
# Opção 1: Passar via variável
terraform apply -var="rds_password=SenhaForte123!"

# Opção 2: Usando arquivo .tfvars (não commitar)
# Criar arquivo: infra/terraform/terraform.tfvars
# rds_password = "SenhaForte123!"
terraform apply
```

---

## Outputs Disponíveis

### Network
```
vpc_id      = "vpc-xxx..."
subnet_ids  = ["subnet-aaa...", "subnet-bbb..."]
```

### Storage
```
bucket_id  = "aiops-locaweb-datalake-2026"
bucket_arn = "arn:aws:s3:::aiops-locaweb-datalake-2026"
```

### Database (quando descomentado)
```
rds_endpoint          = "aiops-gold-db-xxxx.rds.amazonaws.com:5432"
rds_database_name     = "aiops_gold"
rds_username          = "postgres"
glue_catalog_database = "aiops_catalog_db"
```

Acessar outputs:
```bash
terraform output bucket_id
terraform output -json  # Todos em JSON
```

---

## Troubleshooting

### ❌ Erro: "bucket already exists"

Bucket S3 names são **globais e únicos**.

**Solução**: Mudar `bucket_name` em `main.tf`:
```hcl
module "storage" {
  source      = "./modules/storage"
  bucket_name = "aiops-locaweb-datalake-2026-seu-sufixo"  # Adicionar sufixo
}
```

### ❌ Erro: "VPC with cidr 10.0.0.0/16 already exists"

Terraform state desincronizado com AWS.

**Solução**:
```bash
terraform refresh
terraform plan
```

Se persistir, importar recurso existente:
```bash
terraform import aws_vpc.main vpc-xxx...
```

### ❌ Erro: "subnet is not in the same vpc"

Ocorre ao descomentar database com subnets antigas.

**Solução**: Garantir que `module.network.subnet_ids` é usado (não valores hardcoded).

---

## Vantagens da Modularização

| Antes | Depois |
|-------|--------|
| 1 arquivo main.tf com 200+ linhas | main.tf com 25 linhas (legível) |
| Recursos misturados (network + storage + db) | Separação clara de responsabilidades |
| Difícil desativar RDS | Descomentar 1 linha para desativar |
| Não reutilizável | Reusa os mesmos módulos para dev/prod |
| Outputs desorganizados | Outputs estruturados e documentados |

---

## Próximos Passos

1. ✅ Network + Storage rodando
2. ⏳ Descomentar Database quando necessário
3. ⏳ Adicionar mais módulos (ALB, Security Groups, etc)
4. ⏳ Criar ambientes (dev, staging, prod) com arquivos `.tfvars` separados

---

## Referências

- [Terraform Modules Best Practices](https://www.terraform.io/language/modules)
- [AWS Terraform Provider](https://registry.terraform.io/providers/hashicorp/aws)
- CLAUDE.md — Visão geral do projeto
