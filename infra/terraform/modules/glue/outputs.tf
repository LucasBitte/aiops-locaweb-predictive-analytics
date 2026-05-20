output "glue_job_name" {
  description = "Name of the Glue job"
  value       = aws_glue_job.transform_bronze_to_silver.name
}

output "glue_job_arn" {
  description = "ARN of the Glue job"
  value       = aws_glue_job.transform_bronze_to_silver.arn
}

output "glue_role_arn" {
  description = "ARN of the IAM role for Glue"
  value       = var.glue_role_arn != "" ? var.glue_role_arn : aws_iam_role.glue_job_role[0].arn
}

output "script_s3_location" {
  description = "S3 location of the main Glue script"
  value       = "s3://${var.bucket_name}/scripts/transform_bronze_to_silver.py"
}

output "scripts_uploaded" {
  description = "All scripts uploaded to S3 /scripts/ folder"
  value = {
    bronze_upload      = "s3://${var.bucket_name}/scripts/upload_xlsx.py"
    bronze_to_parquet  = "s3://${var.bucket_name}/scripts/xlsx_to_parquet.py"
    silver_transform   = "s3://${var.bucket_name}/scripts/transform_bronze_to_silver.py"
    silver_config      = "s3://${var.bucket_name}/scripts/config.py"
    silver_transforms  = "s3://${var.bucket_name}/scripts/transformations.py"
    silver_validators  = "s3://${var.bucket_name}/scripts/validators.py"
    silver_logger      = "s3://${var.bucket_name}/scripts/logger.py"
  }
}
