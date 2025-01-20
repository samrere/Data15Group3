terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region # Australia region
}

# Use existing role
data "aws_iam_role" "existing_lambda_role" {
  name = "LambdaWebApiRole-DATA15"
}

# Get the Lambda package from S3
data "aws_s3_object" "lambda_package" {
  bucket = "data15group3-scripts"
  key    = "lambda/linkedin_scraper/linkedin_scraper.zip"
}

# Lambda Function
resource "aws_lambda_function" "linkedin_scraper" {
  s3_bucket        = data.aws_s3_object.lambda_package.bucket
  s3_key           = data.aws_s3_object.lambda_package.key
  source_code_hash = data.aws_s3_object.lambda_package.metadata["sha256"]
  function_name    = "linkedin_scraper"
  role            = data.aws_iam_role.existing_lambda_role.arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.12"
  architectures   = ["x86_64"]
  timeout         = 300
  memory_size     = 128

  ephemeral_storage {
    size = 512
  }

  environment {
    variables = {
      ACCOUNT1_EMAIL       = var.account1_email
      ACCOUNT2_EMAIL       = var.account2_email
      ACCOUNT3_EMAIL       = var.account3_email
      SEARCH_LIMIT         = var.search_limit
      JOB_DECORATION_ID    = var.job_decoration_id
      SLEEP_TIME_MIN       = var.sleep_time_min
      SEARCH_LOCATION      = var.search_location
      LINKEDIN_COOKIES_KEY = var.linkedin_cookies_key
      NUMBER_OF_PAGES      = var.number_of_pages
      LISTED_AT            = var.listed_at
      SLEEP_TIME_MAX       = var.sleep_time_max
      LINKEDIN_DATALAKE_KEY = var.linkedin_datalake_key
      ACCOUNT1_COOKIE_FILE = var.account1_cookie_file
      ACCOUNT2_COOKIE_FILE = var.account2_cookie_file
      ACCOUNT3_COOKIE_FILE = var.account3_cookie_file
    }
  }
}

# Lambda Function Retry Configuration
resource "aws_lambda_function_event_invoke_config" "linkedin_scraper_retry" {
  function_name                = aws_lambda_function.linkedin_scraper.function_name
  maximum_event_age_in_seconds = 21600
  maximum_retry_attempts       = 2
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${aws_lambda_function.linkedin_scraper.function_name}"
  retention_in_days = 14
}
