# ==========================================
# 1. REDE (VPC e Conectividade) - ATIVO
# ==========================================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = "aiops-vpc" }
}

# Criando uma Subnet (Necessário para o RDS)
resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  map_public_ip_on_launch = true

  tags = { Name = "aiops-subnet-a" }
}

resource "aws_subnet" "public_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-east-1b"
  map_public_ip_on_launch = true

  tags = { Name = "aiops-subnet-b" }
}

# Internet Gateway para permitir saída de dados (para o seu PC acessar o RDS)
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags   = { Name = "aiops-igw" }
}

# ==========================================
# 2. DATA LAKE (S3) - ATIVO
# ==========================================

resource "aws_s3_bucket" "datalake" {
  bucket = "aiops-locaweb-datalake-2026"
  tags   = { Project = "AIOps Locaweb" }
}

# ==========================================
# 3. INFRAESTRUTURA EM ESPERA - COMENTADO
# (Para evitar custos no Free Tier agora)
# ==========================================

/*
# --- AWS GLUE CATALOG ---
resource "aws_glue_catalog_database" "aiops_catalog" {
  name = "aiops_catalog_db"
}

# --- DB SUBNET GROUP (Obrigatório para RDS em VPC) ---
resource "aws_db_subnet_group" "default" {
  name       = "main"
  subnet_ids = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

# --- AWS RDS (POSTGRESQL) ---
resource "aws_db_instance" "gold_db" {
  allocated_storage    = 20
  db_name              = "aiops_gold"
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = "db.t3.micro"
  username             = "postgres"
  password             = var.rds_password
  db_subnet_group_name = aws_db_subnet_group.default.name
  skip_final_snapshot  = true
  publicly_accessible  = true
}
*/