# Scheduler Module Variables

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

variable "ingestion_job_name" {
  description = "Name of the Cloud Run job to trigger"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for scheduler"
  type        = string
}

variable "ingestion_schedule" {
  description = "Cron schedule for data ingestion (in America/Denver timezone)"
  type        = string
  default     = "0 */6 * * *"  # Every 6 hours
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}
