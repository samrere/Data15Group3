# Create step function role
provider "aws" {
  region = var.aws_region
}

resource "aws_iam_role" "lambda_invocation_role" {
  name = "StepFunctionsLambdaRole-DATA15"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_invocation_policy" {
  name = "LambdaInvocationPolicy"
  role = aws_iam_role.lambda_invocation_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "arn:aws:lambda:ap-southeast-2:863518414180:function:ValidityCheck-starter",
          "arn:aws:lambda:ap-southeast-2:863518414180:function:ValidityCheck-worker",
          "arn:aws:lambda:ap-southeast-2:863518414180:function:ValidityCheck-collector"
        ]
      }
    ]
  })
}