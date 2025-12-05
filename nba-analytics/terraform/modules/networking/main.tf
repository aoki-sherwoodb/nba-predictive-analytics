# Networking Module
# VPC, Subnets, and Serverless VPC Access Connector

# =============================================================================
# VPC NETWORK
# =============================================================================

resource "google_compute_network" "main" {
  name                    = "nba-analytics-vpc-${var.environment}"
  auto_create_subnetworks = false
  description             = "VPC network for NBA Analytics Platform"
}

# =============================================================================
# SUBNET
# =============================================================================

resource "google_compute_subnetwork" "main" {
  name          = "nba-analytics-subnet-${var.environment}"
  ip_cidr_range = var.vpc_cidr
  region        = var.region
  network       = google_compute_network.main.id
  description   = "Subnet for NBA Analytics services"

  private_ip_google_access = true
}

# =============================================================================
# SERVERLESS VPC ACCESS CONNECTOR
# =============================================================================

resource "google_vpc_access_connector" "connector" {
  name          = "nba-vpc-connector-${var.environment}"
  region        = var.region
  ip_cidr_range = var.vpc_connector_cidr
  network       = google_compute_network.main.name

  min_instances = 2
  max_instances = 3

  machine_type = "f1-micro"
}

# =============================================================================
# PRIVATE IP RANGE FOR CLOUD SQL & MEMORYSTORE
# =============================================================================

resource "google_compute_global_address" "private_ip_range" {
  name          = "private-ip-range-${var.environment}"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.main.id
  description   = "Private IP range for Cloud SQL and Memorystore"
}

# =============================================================================
# PRIVATE SERVICES CONNECTION
# =============================================================================

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.main.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}

# =============================================================================
# FIREWALL RULES
# =============================================================================

# Allow internal traffic
resource "google_compute_firewall" "allow_internal" {
  name    = "allow-internal-${var.environment}"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }

  allow {
    protocol = "icmp"
  }

  source_ranges = [var.vpc_cidr, var.vpc_connector_cidr]
  description   = "Allow internal traffic within VPC"
}

# Allow health checks from GCP
resource "google_compute_firewall" "allow_health_checks" {
  name    = "allow-health-checks-${var.environment}"
  network = google_compute_network.main.name

  allow {
    protocol = "tcp"
    ports    = ["8000", "8080", "80", "443"]
  }

  # GCP health check IP ranges
  source_ranges = ["35.191.0.0/16", "130.211.0.0/22"]
  description   = "Allow GCP health checks"
}
