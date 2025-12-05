# Cache Module Variables

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

variable "memory_size_gb" {
  description = "Redis memory size in GB"
  type        = number
}

variable "tier" {
  description = "Redis tier (BASIC or STANDARD_HA)"
  type        = string
}

variable "vpc_id" {
  description = "VPC network ID for private IP"
  type        = string
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}
