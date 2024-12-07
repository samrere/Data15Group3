provider "aws" {
  region = "ap-southeast-2"
}

# Create the S3 Bucket
resource "aws_s3_bucket" "job_data_lake" {
  bucket = "data15group3-job-data-lake" 
  acl    = "private"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "retain-all-files"
    enabled = true
    prefix  = "raw/"
  }

  tags = {
    Name        = "Job Data Lake"
    Environment = "Development"
  }
}

# Configure Server-Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "job_data_lake_encryption" {
  bucket = aws_s3_bucket.job_data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Create Prefix Placeholders
resource "aws_s3_object" "raw_prefix" {
  bucket  = aws_s3_bucket.job_data_lake.id
  key     = "raw/"
  content = ""
}

resource "aws_s3_object" "processed_prefix" {
  bucket  = aws_s3_bucket.job_data_lake.id
  key     = "processed/"
  content = ""
}

resource "aws_s3_object" "analytics_prefix" {
  bucket  = aws_s3_bucket.job_data_lake.id
  key     = "analytics/"
  content = ""
}
