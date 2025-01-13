aws_region     = "ap-southeast-2"
s3_bucket_name = "data15group3-job-data-lake"
s3_base_path   = "raw"

# Database and table configuration
database_name = "linkedin_data_cleaned"
table_name    = "cleaned_jobs_data"

# Crawler configuration
crawler_name     = "linkedin_jobs_data_crawler"
crawler_role_arn = "arn:aws:iam::339713004220:role/service-role/AWSGlueServiceRole-Crawler"
