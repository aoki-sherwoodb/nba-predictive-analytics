# Variable Definitions
# NBA Analytics Platform - GCP Infrastructure

# =============================================================================
# REQUIRED VARIABLES
# =============================================================================

variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

# =============================================================================
# OPTIONAL VARIABLES WITH DEFAULTS
# =============================================================================

variable "region" {
  description = "The GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

variable "db_tier" {
  description = "Cloud SQL instance tier"
  type        = string
  default     = "db-f1-micro"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "nba_analytics"
}

variable "db_user" {
  description = "Database username"
  type        = string
  default     = "app"
}

variable "db_deletion_protection" {
  description = "Enable deletion protection for Cloud SQL"
  type        = bool
  default     = false
}

# =============================================================================
# REDIS CONFIGURATION
# =============================================================================

variable "redis_memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
  default     = 1
}

variable "redis_tier" {
  description = "Redis tier (BASIC or STANDARD_HA)"
  type        = string
  default     = "BASIC"

  validation {
    condition     = contains(["BASIC", "STANDARD_HA"], var.redis_tier)
    error_message = "Redis tier must be BASIC or STANDARD_HA."
  }
}

# =============================================================================
# CLOUD RUN CONFIGURATION
# =============================================================================

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

variable "frontend_cpu" {
  description = "CPU allocation for frontend service"
  type        = string
  default     = "1"
}

variable "frontend_memory" {
  description = "Memory allocation for frontend service"
  type        = string
  default     = "256Mi"
}

variable "frontend_min_instances" {
  description = "Minimum instances for frontend service"
  type        = number
  default     = 0
}

variable "frontend_max_instances" {
  description = "Maximum instances for frontend service"
  type        = number
  default     = 5
}

# =============================================================================
# NETWORKING CONFIGURATION
# =============================================================================

variable "vpc_cidr" {
  description = "CIDR range for the VPC subnet"
  type        = string
  default     = "10.0.0.0/24"
}

variable "vpc_connector_cidr" {
  description = "CIDR range for VPC connector"
  type        = string
  default     = "10.8.0.0/28"
}

# =============================================================================
# LABELS / TAGS
# =============================================================================

variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default = {
    app        = "nba-analytics"
    managed_by = "terraform"
  }
}
