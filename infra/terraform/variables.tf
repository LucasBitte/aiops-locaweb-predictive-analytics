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

variable "rds_password" {
  description = "Senha do banco de dados RDS PostgreSQL"
  type        = string
  sensitive   = true
}