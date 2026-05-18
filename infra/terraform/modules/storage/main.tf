resource "aws_s3_bucket" "datalake" {
  bucket = var.bucket_name
  tags   = { Project = "AIOps Locaweb" }
}
