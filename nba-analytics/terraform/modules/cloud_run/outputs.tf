# Cloud Run Module Outputs

output "api_url" {
  description = "The URL of the API Cloud Run service"
  value       = google_cloud_run_v2_service.api.uri
}

output "api_name" {
  description = "The name of the API Cloud Run service"
  value       = google_cloud_run_v2_service.api.name
}

output "dashboard_url" {
  description = "The URL of the Dashboard Cloud Run service"
  value       = google_cloud_run_v2_service.dashboard.uri
}

output "dashboard_name" {
  description = "The name of the Dashboard Cloud Run service"
  value       = google_cloud_run_v2_service.dashboard.name
}

output "ingestion_job_name" {
  description = "The name of the ingestion Cloud Run job"
  value       = google_cloud_run_v2_job.ingestion.name
}

output "ingestion_job_id" {
  description = "The ID of the ingestion Cloud Run job"
  value       = google_cloud_run_v2_job.ingestion.id
}
