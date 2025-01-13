# Create Lambda execution role
provider "aws" {
  region = var.aws_region
}

resource "aws_iam_role" "lambda_role" {
  name = "LambdaWebApiRole-DATA15"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Attach Athena Full Access
resource "aws_iam_role_policy_attachment" "athena_full_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonAthenaFullAccess"
}

# Attach S3 Full Access
resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# Attach SageMaker Full Access
resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# Attach Lambda basic execution role (for CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}