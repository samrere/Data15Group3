variable "aws_region" {
  description = "AWS region for the resources"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "s3_base_path" {
  description = "Base path in the S3 bucket"
  type        = string
}

variable "database_name" {
  description = "Name of the Glue catalog database"
  type        = string
}

variable "table_name" {
  description = "Name of the Glue catalog table"
  type        = string
}

variable "crawler_name" {
  description = "Name of the Glue crawler"
  type        = string
}

variable "crawler_role_arn" {
  description = "ARN of the IAM role for the Glue crawler"
  type        = string
}
