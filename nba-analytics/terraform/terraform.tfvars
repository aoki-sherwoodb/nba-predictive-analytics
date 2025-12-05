# NBA Analytics Platform - Terraform Variables
# Generated for GCP deployment

# =============================================================================
# REQUIRED - GCP Project Settings
# =============================================================================

# Your GCP project ID
project_id = "finalprojectnba"

# GCP region for resources
region = "us-central1"

# =============================================================================
# Environment Settings
# =============================================================================

# Environment name
environment = "dev"

# =============================================================================
# Database Settings (using cost-effective dev settings)
# =============================================================================

# Cloud SQL tier (db-f1-micro for dev)
db_tier = "db-f1-micro"

# Database name
db_name = "nba_analytics"

# Database user
db_user = "nba_admin"

# =============================================================================
# Redis Settings
# =============================================================================

# Redis memory size in GB
redis_memory_size_gb = 1

# Redis tier (BASIC for dev)
redis_tier = "BASIC"

# =============================================================================
# Cloud Run Settings
# =============================================================================

# API service settings
api_cpu = "1"
api_memory = "512Mi"
api_min_instances = 0
api_max_instances = 10

# Frontend/Dashboard service settings
frontend_cpu = "1"
frontend_memory = "1Gi"
frontend_min_instances = 0
frontend_max_instances = 5

# =============================================================================
# Networking Settings
# =============================================================================

# VPC subnet CIDR
vpc_cidr = "10.0.0.0/24"

# VPC connector CIDR (for serverless access)
vpc_connector_cidr = "10.8.0.0/28"

# =============================================================================
# Labels for resources
# =============================================================================

labels = {
  app        = "nba-analytics"
  managed_by = "terraform"
  team       = "data-engineering"
}
