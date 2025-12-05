# Scheduler Module
# Cloud Scheduler for triggering data ingestion

# =============================================================================
# DATA INGESTION SCHEDULER
# =============================================================================

resource "google_cloud_scheduler_job" "ingestion" {
  name        = "nba-ingestion-${var.environment}"
  description = "Triggers NBA data ingestion job"
  schedule    = var.ingestion_schedule
  time_zone   = "America/Denver"
  region      = var.region

  retry_config {
    retry_count          = 3
    min_backoff_duration = "5s"
    max_backoff_duration = "60s"
    max_retry_duration   = "300s"  # 5 minutes
    max_doublings        = 3
  }

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${var.ingestion_job_name}:run"

    oauth_token {
      service_account_email = var.service_account_email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}

# =============================================================================
# GAME DAY SCHEDULER (More frequent during NBA season)
# =============================================================================

resource "google_cloud_scheduler_job" "gameday_ingestion" {
  name        = "nba-gameday-ingestion-${var.environment}"
  description = "More frequent ingestion during game times (6PM-12AM MT)"
  schedule    = "*/30 18-23 * 10,11,12,1,2,3,4,5,6 *"  # Every 30 mins, 6PM-midnight, Oct-June (NBA season)
  time_zone   = "America/Denver"
  region      = var.region

  retry_config {
    retry_count          = 2
    min_backoff_duration = "10s"
    max_backoff_duration = "60s"
    max_retry_duration   = "180s"
    max_doublings        = 2
  }

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${var.ingestion_job_name}:run"

    oauth_token {
      service_account_email = var.service_account_email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }
}
