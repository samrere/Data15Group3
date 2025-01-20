variable "aws_region" {
  description = "AWS region"
  type        = string
}
variable "account1_email" {
  description = "Email for account 1"
  type        = string
}

variable "account2_email" {
  description = "Email for account 2"
  type        = string
}

variable "account3_email" {
  description = "Email for account 3"
  type        = string
}

variable "search_limit" {
  description = "Search limit for LinkedIn jobs"
  type        = string
}

variable "job_decoration_id" {
  description = "Job decoration ID for LinkedIn API"
  type        = string
}

variable "sleep_time_min" {
  description = "Minimum sleep time between requests"
  type        = string
}

variable "search_location" {
  description = "Location for job search"
  type        = string
}

variable "linkedin_cookies_key" {
  description = "S3 bucket key for LinkedIn cookies"
  type        = string
}

variable "number_of_pages" {
  description = "Number of pages to scrape"
  type        = string
}

variable "listed_at" {
  description = "Listed at time filter"
  type        = string
}

variable "sleep_time_max" {
  description = "Maximum sleep time between requests"
  type        = string
}

variable "linkedin_datalake_key" {
  description = "S3 bucket key for LinkedIn data lake"
  type        = string
}

variable "account1_cookie_file" {
  description = "Cookie file name for account 1"
  type        = string
}

variable "account2_cookie_file" {
  description = "Cookie file name for account 2"
  type        = string
}

variable "account3_cookie_file" {
  description = "Cookie file name for account 3"
  type        = string
}