# Configure AWS Provider
provider "aws" {
  region = "ap-southeast-2" # Change to your desired region
}

# Create AWS Glue Database
resource "aws_glue_catalog_database" "jobs_database" {
  name        = "jobs_database_test"
  description = "Database for job information data in Parquet format"
}

# Create AWS Glue Table Schema
resource "aws_glue_catalog_table" "jobs_table" {
  name          = "cleaned_jobs_data"
  database_name = aws_glue_catalog_database.jobs_database.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL              = "TRUE"
    "classification"      = "parquet"
    "parquet.compression" = "SNAPPY"
    "connectionName"      = ""
  }

  storage_descriptor {
    location      = "s3://crawler-test-rowan/data/" # Replace with your S3 bucket path
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }


    columns {
      name = "title"
      type = "string"
    }
    columns {
      name = "company"
      type = "string"
    }
    columns {
      name = "location"
      type = "string"
    }
    columns {
      name = "employment_type"
      type = "string"
    }
    columns {
      name = "seniority_level"
      type = "string"
    }
    columns {
      name = "industries"
      type = "array<string>"
    }
    columns {
      name = "job_functions"
      type = "array<string>"
    }
    columns {
      name = "applies"
      type = "bigint"
    }
    columns {
      name = "workplace_type"
      type = "string"
    }
    columns {
      name = "description"
      type = "string"
    }
    columns {
      name = "skills"
      type = "array<string>"
    }
    columns {
      name = "job_url"
      type = "string"
    }
    columns {
      name = "reposted"
      type = "boolean"
    }
    columns {
      name = "posted_time"
      type = "string"
    }
    columns {
      name = "posted_time_epoch"
      type = "bigint"
    }
    columns {
      name = "expire_time"
      type = "string"
    }
    columns {
      name = "expire_time_epoch"
      type = "bigint"
    }
    columns {
      name = "apply_url"
      type = "string"
    }
  }
}

# Rest of the configuration (IAM roles and crawler) remains the same
resource "aws_glue_crawler" "jobs_crawler" {
  database_name = aws_glue_catalog_database.jobs_database.name
  name          = "jobs_data_crawler"
  role          = "arn:aws:iam::863518414180:role/imba-glue-crawler-GlueServiceRole-DNd83nj237Wi" # Replace with your existing role ARN

  s3_target {
    path = "s3://crawler-test-rowan/data/" # Replace with your S3 bucket path
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  #schedule = "cron(0 12 * * ? *)" # Runs daily at 12:00 PM UTC
}