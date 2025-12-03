# Cloud Run Module
# Deploys API and Dashboard services

# =============================================================================
# API SERVICE
# =============================================================================

resource "google_cloud_run_v2_service" "api" {
  name     = "nba-analytics-api-${var.environment}"
  location = var.region

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = var.api_min_instances
      max_instance_count = var.api_max_instances
    }

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${var.artifact_registry_url}/api:latest"

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = var.api_cpu
          memory = var.api_memory
        }
      }

      # Environment variables
      env {
        name  = "USE_CLOUD_SQL"
        value = "true"
      }

      env {
        name  = "DB_HOST"
        value = "/cloudsql/${var.db_connection_name}"
      }

      env {
        name  = "DB_NAME"
        value = var.db_name
      }

      env {
        name  = "DB_USER"
        value = var.db_user
      }

      env {
        name = "DB_PASSWORD"
        value_source {
          secret_key_ref {
            secret  = var.db_password_secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "REDIS_HOST"
        value = var.redis_host
      }

      env {
        name  = "REDIS_PORT"
        value = tostring(var.redis_port)
      }

      env {
        name  = "MODEL_STORAGE_BACKEND"
        value = "gcs"
      }

      env {
        name  = "MODEL_BUCKET"
        value = var.model_bucket_name
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }

      env {
        name  = "API_DEBUG"
        value = var.environment == "dev" ? "true" : "false"
      }

      # Cloud SQL proxy connection
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
    }

    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [var.db_connection_name]
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }
}

# =============================================================================
# DASHBOARD SERVICE
# =============================================================================

resource "google_cloud_run_v2_service" "dashboard" {
  name     = "nba-analytics-dashboard-${var.environment}"
  location = var.region

  template {
    service_account = var.service_account_email

    scaling {
      min_instance_count = var.dashboard_min_instances
      max_instance_count = var.dashboard_max_instances
    }

    vpc_access {
      connector = var.vpc_connector_id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${var.artifact_registry_url}/dashboard:latest"

      ports {
        container_port = 8501
      }

      resources {
        limits = {
          cpu    = var.dashboard_cpu
          memory = var.dashboard_memory
        }
      }

      # Environment variables
      env {
        name  = "API_URL"
        value = google_cloud_run_v2_service.api.uri
      }

      env {
        name  = "ENVIRONMENT"
        value = var.environment
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
    ]
  }

  depends_on = [google_cloud_run_v2_service.api]
}

# =============================================================================
# INGESTION JOB SERVICE
# =============================================================================

resource "google_cloud_run_v2_job" "ingestion" {
  name     = "nba-analytics-ingestion-${var.environment}"
  location = var.region

  template {
    template {
      service_account = var.service_account_email

      vpc_access {
        connector = var.vpc_connector_id
        egress    = "PRIVATE_RANGES_ONLY"
      }

      containers {
        image = "${var.artifact_registry_url}/api:latest"

        command = ["python", "-m", "scripts.run_ingestion"]

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }

        # Environment variables (same as API)
        env {
          name  = "USE_CLOUD_SQL"
          value = "true"
        }

        env {
          name  = "DB_HOST"
          value = "/cloudsql/${var.db_connection_name}"
        }

        env {
          name  = "DB_NAME"
          value = var.db_name
        }

        env {
          name  = "DB_USER"
          value = var.db_user
        }

        env {
          name = "DB_PASSWORD"
          value_source {
            secret_key_ref {
              secret  = var.db_password_secret_id
              version = "latest"
            }
          }
        }

        env {
          name  = "REDIS_HOST"
          value = var.redis_host
        }

        env {
          name  = "REDIS_PORT"
          value = tostring(var.redis_port)
        }

        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
      }

      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [var.db_connection_name]
        }
      }

      max_retries = 3
      timeout     = "1800s"  # 30 minutes
    }
  }

  labels = var.labels

  lifecycle {
    ignore_changes = [
      template[0].template[0].containers[0].image,
    ]
  }
}

# =============================================================================
# IAM - PUBLIC ACCESS FOR DASHBOARD
# =============================================================================

# Allow unauthenticated access to Dashboard
resource "google_cloud_run_v2_service_iam_member" "dashboard_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.dashboard.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Allow unauthenticated access to API
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
