# Cloud Run Module Variables

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_connector_id" {
  description = "VPC connector ID for private network access"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for Cloud Run services"
  type        = string
}

variable "artifact_registry_url" {
  description = "Artifact Registry URL for container images"
  type        = string
}

# Database Configuration
variable "db_connection_name" {
  description = "Cloud SQL connection name"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_user" {
  description = "Database user"
  type        = string
}

variable "db_password_secret_id" {
  description = "Secret Manager secret ID for database password"
  type        = string
}

# Redis Configuration
variable "redis_host" {
  description = "Redis host IP"
  type        = string
}

variable "redis_port" {
  description = "Redis port"
  type        = number
}

# Storage Configuration
variable "model_bucket_name" {
  description = "GCS bucket name for ML models"
  type        = string
}

# API Service Configuration
variable "api_cpu" {
  description = "CPU allocation for API service"
  type        = string
  default     = "1"
}

variable "api_memory" {
  description = "Memory allocation for API service"
  type        = string
  default     = "512Mi"
}

variable "api_min_instances" {
  description = "Minimum instances for API service"
  type        = number
  default     = 0
}

variable "api_max_instances" {
  description = "Maximum instances for API service"
  type        = number
  default     = 10
}

# Dashboard Service Configuration
variable "dashboard_cpu" {
  description = "CPU allocation for Dashboard service"
  type        = string
  default     = "1"
}

variable "dashboard_memory" {
  description = "Memory allocation for Dashboard service"
  type        = string
  default     = "1Gi"
}

variable "dashboard_min_instances" {
  description = "Minimum instances for Dashboard service"
  type        = number
  default     = 0
}

variable "dashboard_max_instances" {
  description = "Maximum instances for Dashboard service"
  type        = number
  default     = 5
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}
