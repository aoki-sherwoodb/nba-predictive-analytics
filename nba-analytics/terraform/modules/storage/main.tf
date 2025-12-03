# Storage Module
# GCS Bucket for ML Models

# =============================================================================
# GCS BUCKET FOR ML MODELS
# =============================================================================

resource "google_storage_bucket" "models" {
  name     = "${var.project_id}-ml-models-${var.environment}"
  location = var.region

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      num_newer_versions = 5  # Keep last 5 versions of each model
    }
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      days_since_noncurrent_time = 90  # Delete non-current versions after 90 days
    }
  }

  labels = var.labels
}

# =============================================================================
# IAM BINDINGS
# =============================================================================

# Allow Cloud Run service account to read/write models
resource "google_storage_bucket_iam_member" "cloud_run_access" {
  bucket = google_storage_bucket.models.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.cloud_run_sa_email}"
}

# =============================================================================
# INITIAL FOLDERS (using empty objects)
# =============================================================================

resource "google_storage_bucket_object" "models_folder" {
  name    = "models/"
  bucket  = google_storage_bucket.models.name
  content = " "  # Empty content to create folder
}

resource "google_storage_bucket_object" "checkpoints_folder" {
  name    = "checkpoints/"
  bucket  = google_storage_bucket.models.name
  content = " "
}
