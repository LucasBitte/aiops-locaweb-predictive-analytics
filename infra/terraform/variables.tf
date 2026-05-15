variable "aws_region" {
  description = "Região da AWS"
  type        = string
  default     = "us-east-1"
}

variable "aws_profile" {
  description = "Perfil do AWS CLI"
  type        = string
  default     = "aiops-project"
}

variable "bucket_name" {
  description = "Nome único do bucket S3"
  type        = string
  default     = "aiops-locaweb-datalake-2026" # <--- MUDE ESTE NOME (deve ser único globalmente)
}