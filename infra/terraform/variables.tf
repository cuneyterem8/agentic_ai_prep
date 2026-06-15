variable "aws_region" {
  type    = string
  default = "eu-central-1"
}

variable "project_name" {
  type    = string
  default = "agenticai-ing-prep"
}

variable "environment" {
  type    = string
  default = "staging"
}

variable "app_version" {
  type    = string
  default = "0.1.0"
}

variable "container_image" {
  description = "ECR image URI. CI deploy adımı bunu set eder."
  type        = string
  default     = ""
}

variable "openai_api_key" {
  type      = string
  sensitive = true
  default   = ""
}

variable "llm_provider" {
  type    = string
  default = "mock"
}

variable "desired_count" {
  type    = number
  default = 1
}

variable "log_retention_days" {
  type    = number
  default = 14
}

variable "db_username" {
  type    = string
  default = "agenticai"
}

variable "db_password" {
  type      = string
  sensitive = true
}

variable "db_name" {
  type    = string
  default = "agenticai"
}
