# Criação do Bucket S3 (Data Lake)
resource "aws_s3_bucket" "datalake" {
  bucket = var.bucket_name

  tags = {
    Project    = "AIOps Locaweb"
    ManagedBy  = "Terraform"
    Environment = "Portfolio"
  }
}

# Bloqueio de Acesso Público (Segurança é o que recrutador mais olha!)
resource "aws_s3_bucket_public_access_block" "security" {
  bucket = aws_s3_bucket.datalake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versionamento para evitar perda de dados
resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.datalake.id
  versioning_configuration {
    status = "Enabled"
  }
}