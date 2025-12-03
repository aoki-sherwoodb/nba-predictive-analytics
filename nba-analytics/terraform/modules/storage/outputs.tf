# Storage Module Outputs

output "bucket_name" {
  description = "The name of the GCS bucket"
  value       = google_storage_bucket.models.name
}

output "bucket_url" {
  description = "The URL of the GCS bucket"
  value       = google_storage_bucket.models.url
}

output "bucket_self_link" {
  description = "The self link of the GCS bucket"
  value       = google_storage_bucket.models.self_link
}
