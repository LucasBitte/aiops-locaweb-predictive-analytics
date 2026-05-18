output "bucket_id" {
  value       = aws_s3_bucket.datalake.id
  description = "Nome/ID do bucket S3"
}

output "bucket_arn" {
  value       = aws_s3_bucket.datalake.arn
  description = "ARN do bucket S3"
}
