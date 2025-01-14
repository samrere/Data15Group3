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

variable "crawler_policy_name" {
  description = "Name of the Glue Crawler"
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

variable "glue_security_configuration_name" {
  description = "Name of the Glue Security Configuration"
  type        = string
}



