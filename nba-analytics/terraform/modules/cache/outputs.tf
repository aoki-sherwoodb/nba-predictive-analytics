# Cache Module Outputs

output "redis_host" {
  description = "The IP address of the Redis instance"
  value       = google_redis_instance.main.host
}

output "redis_port" {
  description = "The port number of the Redis instance"
  value       = google_redis_instance.main.port
}

output "redis_id" {
  description = "The ID of the Redis instance"
  value       = google_redis_instance.main.id
}

output "redis_name" {
  description = "The name of the Redis instance"
  value       = google_redis_instance.main.name
}

output "current_location_id" {
  description = "The current zone where the Redis endpoint is placed"
  value       = google_redis_instance.main.current_location_id
}
