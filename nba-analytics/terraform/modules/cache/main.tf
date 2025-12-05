# Cache Module
# Memorystore for Redis

# =============================================================================
# MEMORYSTORE REDIS INSTANCE
# =============================================================================

resource "google_redis_instance" "main" {
  name           = "nba-analytics-cache-${var.environment}"
  tier           = var.tier
  memory_size_gb = var.memory_size_gb
  region         = var.region

  authorized_network = var.vpc_id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"

  redis_version = "REDIS_7_0"

  display_name = "NBA Analytics Redis Cache"

  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 3
        minutes = 0
      }
    }
  }

  labels = var.labels
}
