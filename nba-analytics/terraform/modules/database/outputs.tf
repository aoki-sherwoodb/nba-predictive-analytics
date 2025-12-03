# Database Module Outputs

output "instance_name" {
  description = "The name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.name
}

output "connection_name" {
  description = "The connection name for Cloud SQL (project:region:instance)"
  value       = google_sql_database_instance.main.connection_name
}

output "private_ip" {
  description = "The private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "database_name" {
  description = "The name of the database"
  value       = google_sql_database.main.name
}

output "user_name" {
  description = "The database username"
  value       = google_sql_user.app.name
}

output "password_secret_id" {
  description = "The Secret Manager secret ID for the database password"
  value       = google_secret_manager_secret.db_password.secret_id
}

output "password_secret_version" {
  description = "The Secret Manager secret version"
  value       = google_secret_manager_secret_version.db_password.name
}
