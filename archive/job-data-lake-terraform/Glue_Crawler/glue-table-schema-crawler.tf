provider "aws" {
  region = var.aws_region
}

resource "aws_glue_catalog_database" "jobs_database" {
  name        = var.database_name
  description = "Database for job information data in Parquet format"
}

resource "aws_glue_catalog_table" "jobs_table" {
  name          = var.table_name
  database_name = aws_glue_catalog_database.jobs_database.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL              = "TRUE"
    "classification"      = "avro"
    "connectionName"      = ""
  }

  partition_keys {
    name = "year"
    type = "string"
  }

  partition_keys {
    name = "month"
    type = "string"
  }

  partition_keys {
    name = "day"
    type = "string"
  }

  partition_keys {
    name = "keyword"
    type = "string"
  }

  storage_descriptor {
    location      = "s3://${var.s3_bucket_name}/${var.s3_base_path}/"
    input_format  = "org.apache.hadoop.hive.ql.io.avro.AvroContainerInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.avro.AvroContainerOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.serde2.avro.AvroSerDe"
    }

    columns {
      name = "job_id"
      type = "string"
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
      type = "bigint"
    }
    columns {
      name = "expire_time"
      type = "bigint"
    }
    columns {
      name = "apply_url"
      type = "string"
    }
  }
}

# Create Glue Security Configuration
resource "aws_glue_security_configuration" "crawler_security" {
  name = "glue-security-config"

  encryption_configuration {
    cloudwatch_encryption {
      cloudwatch_encryption_mode = "DISABLED"
    }

    job_bookmarks_encryption {
      job_bookmarks_encryption_mode = "DISABLED"
    }

    s3_encryption {
      s3_encryption_mode = "SSE-S3"
    }
  }
}


resource "aws_glue_crawler" "jobs_crawler" {
  database_name = aws_glue_catalog_database.jobs_database.name
  name          = var.crawler_name
  role          = var.crawler_role_arn
  security_configuration = aws_glue_security_configuration.crawler_security.name

  catalog_target {
    database_name = aws_glue_catalog_database.jobs_database.name
    tables        = [aws_glue_catalog_table.jobs_table.name]
  }
  configuration = jsonencode(
    {
      Grouping = {
        TableGroupingPolicy = "CombineCompatibleSchemas"
      }
      CrawlerOutput = {
        Partitions = { AddOrUpdateBehavior = "InheritFromTable" }
      }
      Version = 1
    }
  )
  
  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "LOG"
  }

}