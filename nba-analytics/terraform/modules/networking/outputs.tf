# Networking Module Outputs

output "vpc_id" {
  description = "The ID of the VPC"
  value       = google_compute_network.main.id
}

output "vpc_name" {
  description = "The name of the VPC"
  value       = google_compute_network.main.name
}

output "subnet_id" {
  description = "The ID of the subnet"
  value       = google_compute_subnetwork.main.id
}

output "subnet_name" {
  description = "The name of the subnet"
  value       = google_compute_subnetwork.main.name
}

output "vpc_connector_id" {
  description = "The ID of the VPC connector"
  value       = google_vpc_access_connector.connector.id
}

output "vpc_connector_name" {
  description = "The name of the VPC connector"
  value       = google_vpc_access_connector.connector.name
}

output "private_vpc_connection" {
  description = "The private VPC connection for managed services"
  value       = google_service_networking_connection.private_vpc_connection.id
}
