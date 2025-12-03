# Root Module Outputs
# Exposes key infrastructure values for reference and CI/CD

# =============================================================================
# PROJECT INFORMATION
# =============================================================================

output "project_id" {
  description = "GCP Project ID"
  value       = var.project_id
}

output "region" {
  description = "GCP Region"
  value       = var.region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

# =============================================================================
# NETWORKING OUTPUTS
# =============================================================================

output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.networking.vpc_id
}

output "vpc_name" {
  description = "The name of the VPC"
  value       = module.networking.vpc_name
}

output "vpc_connector_id" {
  description = "The VPC connector ID for serverless access"
  value       = module.networking.vpc_connector_id
}

# =============================================================================
# DATABASE OUTPUTS
# =============================================================================

output "db_connection_name" {
  description = "Cloud SQL connection name for Cloud Run"
  value       = module.database.connection_name
}

output "db_private_ip" {
  description = "Private IP of the Cloud SQL instance"
  value       = module.database.private_ip
  sensitive   = true
}

output "db_password_secret_id" {
  description = "Secret Manager ID for database password"
  value       = module.database.password_secret_id
}

# =============================================================================
# CACHE OUTPUTS
# =============================================================================

output "redis_host" {
  description = "Redis host IP"
  value       = module.cache.redis_host
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = module.cache.redis_port
}

# =============================================================================
# STORAGE OUTPUTS
# =============================================================================

output "model_bucket_name" {
  description = "GCS bucket for ML models"
  value       = module.storage.bucket_name
}

output "model_bucket_url" {
  description = "GCS bucket URL for ML models"
  value       = module.storage.bucket_url
}

# =============================================================================
# CLOUD RUN OUTPUTS
# =============================================================================

output "api_url" {
  description = "URL of the API Cloud Run service"
  value       = module.cloud_run.api_url
}

output "dashboard_url" {
  description = "URL of the Dashboard Cloud Run service"
  value       = module.cloud_run.dashboard_url
}

output "api_service_name" {
  description = "Name of the API Cloud Run service"
  value       = module.cloud_run.api_name
}

output "dashboard_service_name" {
  description = "Name of the Dashboard Cloud Run service"
  value       = module.cloud_run.dashboard_name
}

output "ingestion_job_name" {
  description = "Name of the ingestion Cloud Run job"
  value       = module.cloud_run.ingestion_job_name
}

# =============================================================================
# SCHEDULER OUTPUTS
# =============================================================================

output "ingestion_scheduler_name" {
  description = "Name of the regular ingestion scheduler"
  value       = module.scheduler.ingestion_scheduler_name
}

output "gameday_scheduler_name" {
  description = "Name of the gameday ingestion scheduler"
  value       = module.scheduler.gameday_scheduler_name
}

# =============================================================================
# ARTIFACT REGISTRY
# =============================================================================

output "artifact_registry_url" {
  description = "URL for pushing container images"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.containers.repository_id}"
}

# =============================================================================
# SERVICE ACCOUNTS
# =============================================================================

output "cloud_run_service_account_email" {
  description = "Email of the Cloud Run service account"
  value       = google_service_account.cloud_run.email
}
