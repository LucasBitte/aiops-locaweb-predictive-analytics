variable "bucket_name" {
  description = "S3 bucket name for Bronze/Silver data lake"
  type        = string
}

variable "glue_role_arn" {
  description = "ARN of existing IAM role for Glue (if not provided, will create one)"
  type        = string
  default     = ""
}

variable "glue_job_name" {
  description = "Name of the Glue job"
  type        = string
  default     = "transform_bronze_to_silver"
}

variable "glue_version" {
  description = "Glue version (e.g., 4.0)"
  type        = string
  default     = "4.0"
}

variable "worker_type" {
  description = "Worker type: G.1X (1 DPU) or G.2X (2 DPU)"
  type        = string
  default     = "G.1X"

  validation {
    condition     = contains(["G.1X", "G.2X"], var.worker_type)
    error_message = "Worker type must be G.1X or G.2X"
  }
}

variable "num_workers" {
  description = "Number of workers (Free Tier: max 3 × G.1X = 180 DPU-min)"
  type        = number
  default     = 3

  validation {
    condition     = var.num_workers >= 2 && var.num_workers <= 10
    error_message = "Number of workers must be between 2 and 10"
  }
}

variable "timeout_minutes" {
  description = "Job timeout in minutes (for 41.4k records: 60 min sufficient)"
  type        = number
  default     = 60

  validation {
    condition     = var.timeout_minutes >= 1 && var.timeout_minutes <= 2880
    error_message = "Timeout must be between 1 and 2880 minutes"
  }
}
