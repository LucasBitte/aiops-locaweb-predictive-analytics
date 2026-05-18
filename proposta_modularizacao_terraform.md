# Proposta de Modularização do Terraform - Projeto AIOps

Atualmente, a infraestrutura do **Projeto AIOps Locaweb** está concentrada em um único arquivo (`infra/terraform/main.tf`), misturando recursos de Rede (VPC), Storage (S3) e Banco de Dados (RDS e Glue). 

Utilizando o guia de modularização passo a passo, podemos reestruturar este código para deixá-lo em conformidade com as melhores práticas de mercado.

## 1. Módulos Propostos

Para este projeto, a separação ideal seria criar 3 (três) módulos principais dentro de `infra/terraform/modules/`:

1. **`network`**: Conterá a VPC, Subnets (A e B) e o Internet Gateway.
2. **`storage`**: Conterá o Bucket S3 (Data Lake).
3. **`database`**: Conterá o DB Subnet Group, o banco RDS PostgreSQL (Gold) e o AWS Glue Catalog.

---

## 2. Passo a Passo da Refatoração

### Passo 1: Criar a Estrutura de Pastas
Na raiz `infra/terraform/`, crie as pastas:
```text
modules/
 ├── network/
 ├── storage/
 └── database/
```

### Passo 2: Módulo `network` (Rede)
1. Crie `modules/network/main.tf` e mova os blocos `aws_vpc`, `aws_subnet` e `aws_internet_gateway` do arquivo original para cá.
2. Crie `modules/network/outputs.tf` para exportar os IDs necessários:
```hcl
output "vpc_id" {
  value = aws_vpc.main.id
}
output "subnet_ids" {
  value = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}
```

### Passo 3: Módulo `storage` (Data Lake)
1. Crie `modules/storage/main.tf` e mova o bloco `aws_s3_bucket.datalake` para cá.
2. Crie `modules/storage/variables.tf` para permitir que o nome do bucket seja injetado via variável (evita chumbamento de strings no módulo).
3. Crie `modules/storage/outputs.tf` exportando o nome do bucket para uso futuro.

### Passo 4: Módulo `database` (RDS e Glue)
1. Crie `modules/database/main.tf` e mova os blocos comentados do RDS, DB Subnet Group e Glue Catalog.
2. Crie `modules/database/variables.tf`. Este módulo dependerá da rede, então ele precisará receber:
```hcl
variable "subnet_ids" { type = list(string) }
variable "rds_password" { type = string, sensitive = true }
```
3. No `main.tf` deste módulo, altere o DB Subnet Group para usar a variável: `subnet_ids = var.subnet_ids`.

### Passo 5: Orquestração no Root (`main.tf` raiz)
Substitua o conteúdo atual do seu `infra/terraform/main.tf` por chamadas de módulo:

```hcl
# main.tf (Raiz)

module "network" {
  source = "./modules/network"
}

module "storage" {
  source = "./modules/storage"
  bucket_name = "aiops-locaweb-datalake-2026"
}

# Só descomente/aplique quando for usar para não gerar custos
/*
module "database" {
  source       = "./modules/database"
  subnet_ids   = module.network.subnet_ids # Dependência explícita via output
  rds_password = var.rds_password
}
*/
```

---

## 3. Vantagens desta Refatoração

1. **Controle de Custos**: Você pode comentar apenas a chamada `module "database" { ... }` na raiz. A rede e o S3 continuam de pé (não geram custos no free tier), mas o RDS (que gera custos) fica desligado, sem precisar comentar dezenas de linhas de código.
2. **Reutilização**: Se futuramente você quiser subir um ambiente de `dev` e outro de `prod`, você usa os mesmos módulos apenas passando variáveis diferentes.
3. **Organização**: O arquivo principal fica com apenas 15 linhas, fáceis de ler, mostrando a macroarquitetura do projeto de cima para baixo.
