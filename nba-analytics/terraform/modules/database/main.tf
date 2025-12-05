# Database Module
# Cloud SQL PostgreSQL Instance

# =============================================================================
# RANDOM PASSWORD GENERATION
# =============================================================================

resource "random_password" "db_password" {
  length  = 32
  special = false
}

# =============================================================================
# CLOUD SQL INSTANCE
# =============================================================================

resource "google_sql_database_instance" "main" {
  name             = "nba-analytics-db-${var.environment}"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = var.db_tier

    ip_configuration {
      ipv4_enabled    = false
      private_network = var.vpc_id
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = var.environment == "prod"

      backup_retention_settings {
        retained_backups = var.environment == "prod" ? 14 : 7
      }
    }

    maintenance_window {
      day          = 7  # Sunday
      hour         = 3  # 3 AM
      update_track = "stable"
    }

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    insights_config {
      query_insights_enabled  = var.environment == "prod"
      record_application_tags = var.environment == "prod"
      record_client_address   = var.environment == "prod"
    }

    user_labels = var.labels
  }

  deletion_protection = var.deletion_protection

  depends_on = [var.private_vpc_connection]
}

# =============================================================================
# DATABASE
# =============================================================================

resource "google_sql_database" "main" {
  name     = var.db_name
  instance = google_sql_database_instance.main.name
}

# =============================================================================
# DATABASE USER
# =============================================================================

resource "google_sql_user" "app" {
  name     = var.db_user
  instance = google_sql_database_instance.main.name
  password = random_password.db_password.result
}

# =============================================================================
# SECRET MANAGER - STORE DB PASSWORD
# =============================================================================

resource "google_secret_manager_secret" "db_password" {
  secret_id = "db-password-${var.environment}"

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret_version" "db_password" {
  secret      = google_secret_manager_secret.db_password.id
  secret_data = random_password.db_password.result
}
