# Scheduler Module Outputs

output "ingestion_scheduler_name" {
  description = "The name of the regular ingestion scheduler job"
  value       = google_cloud_scheduler_job.ingestion.name
}

output "ingestion_scheduler_id" {
  description = "The ID of the regular ingestion scheduler job"
  value       = google_cloud_scheduler_job.ingestion.id
}

output "gameday_scheduler_name" {
  description = "The name of the gameday ingestion scheduler job"
  value       = google_cloud_scheduler_job.gameday_ingestion.name
}

output "gameday_scheduler_id" {
  description = "The ID of the gameday ingestion scheduler job"
  value       = google_cloud_scheduler_job.gameday_ingestion.id
}
