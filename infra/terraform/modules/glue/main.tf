# ==========================================
# AWS GLUE JOB: Bronze → Silver Transformation
# Épico: E5
# Worker: G.1X × 3 (Free Tier compliant)
# ==========================================

# --- IAM ROLE para Glue (apenas se não fornecida externamente) ---
resource "aws_iam_role" "glue_job_role" {
  count = var.glue_role_arn == "" ? 1 : 0
  name  = "aiops-glue-bronze-silver-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = "AIOps Locaweb"
    Epic    = "E5"
  }
}

# --- IAM POLICY: S3 Access (Bronze + Silver) (apenas se não fornecida externamente) ---
resource "aws_iam_role_policy" "glue_s3_policy" {
  count = var.glue_role_arn == "" ? 1 : 0
  name  = "aiops-glue-s3-access"
  role  = aws_iam_role.glue_job_role[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.bucket_name}",
          "arn:aws:s3:::${var.bucket_name}/*"
        ]
      }
    ]
  })
}

# --- IAM POLICY: CloudWatch Logs (required by Glue) (apenas se não fornecida externamente) ---
resource "aws_iam_role_policy_attachment" "glue_logs_policy" {
  count      = var.glue_role_arn == "" ? 1 : 0
  role       = aws_iam_role.glue_job_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

# --- Upload script Python para S3 ---
resource "aws_s3_object" "glue_script_transform" {
  bucket = var.bucket_name
  key    = "scripts/transform_bronze_to_silver.py"
  source = "${path.module}/../../../../pipeline/silver/transform_bronze_to_silver.py"

  etag = filemd5("${path.module}/../../../../pipeline/silver/transform_bronze_to_silver.py")

  tags = {
    Project = "AIOps Locaweb"
    Epic    = "E5"
  }
}

# --- Upload módulos suportadores para S3 ---
resource "aws_s3_object" "glue_module_config" {
  bucket = var.bucket_name
  key    = "scripts/config.py"
  source = "${path.module}/../../../../pipeline/silver/config.py"
  etag   = filemd5("${path.module}/../../../../pipeline/silver/config.py")
}

resource "aws_s3_object" "glue_module_transformations" {
  bucket = var.bucket_name
  key    = "scripts/transformations.py"
  source = "${path.module}/../../../../pipeline/silver/transformations.py"
  etag   = filemd5("${path.module}/../../../../pipeline/silver/transformations.py")
}

resource "aws_s3_object" "glue_module_validators" {
  bucket = var.bucket_name
  key    = "scripts/validators.py"
  source = "${path.module}/../../../../pipeline/silver/validators.py"
  etag   = filemd5("${path.module}/../../../../pipeline/silver/validators.py")
}

resource "aws_s3_object" "glue_module_logger" {
  bucket = var.bucket_name
  key    = "scripts/logger.py"
  source = "${path.module}/../../../../pipeline/silver/logger.py"
  etag   = filemd5("${path.module}/../../../../pipeline/silver/logger.py")
}

# --- Upload script de conversão Bronze (E4→E5) ---
resource "aws_s3_object" "glue_script_xlsx_to_parquet" {
  bucket = var.bucket_name
  key    = "scripts/xlsx_to_parquet.py"
  source = "${path.module}/../../../../pipeline/bronze/xlsx_to_parquet.py"
  etag   = filemd5("${path.module}/../../../../pipeline/bronze/xlsx_to_parquet.py")

  tags = {
    Project = "AIOps Locaweb"
    Epic    = "E4-E5"
    Stage   = "Bronze"
  }
}

# --- Upload script de upload XLSX (E4) ---
resource "aws_s3_object" "glue_script_upload_xlsx" {
  bucket = var.bucket_name
  key    = "scripts/upload_xlsx.py"
  source = "${path.module}/../../../../pipeline/bronze/upload_xlsx.py"
  etag   = filemd5("${path.module}/../../../../pipeline/bronze/upload_xlsx.py")

  tags = {
    Project = "AIOps Locaweb"
    Epic    = "E4"
    Stage   = "Bronze"
  }
}

# --- AWS GLUE JOB ---
resource "aws_glue_job" "transform_bronze_to_silver" {
  name              = var.glue_job_name
  role_arn          = var.glue_role_arn != "" ? var.glue_role_arn : aws_iam_role.glue_job_role[0].arn
  glue_version      = var.glue_version
  worker_type       = var.worker_type
  number_of_workers = var.num_workers
  timeout           = var.timeout_minutes
  max_retries       = 0

  command {
    name            = "glueetl"
    script_location = "s3://${var.bucket_name}/scripts/transform_bronze_to_silver.py"
    python_version  = "3"
  }

  # Dependências dos scripts S3
  depends_on = [
    aws_s3_object.glue_script_transform,
    aws_s3_object.glue_script_xlsx_to_parquet,
    aws_s3_object.glue_script_upload_xlsx,
    aws_s3_object.glue_module_config,
    aws_s3_object.glue_module_transformations,
    aws_s3_object.glue_module_validators,
    aws_s3_object.glue_module_logger
  ]

  tags = {
    Project     = "AIOps Locaweb"
    Epic        = "E5"
    Pipeline    = "Bronze-Silver"
    Environment = "production"
  }
}
