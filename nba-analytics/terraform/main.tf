# Main Terraform Configuration
# NBA Analytics Platform - GCP Infrastructure

# =============================================================================
# ENABLE REQUIRED APIS
# =============================================================================

resource "google_project_service" "required_apis" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "redis.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "vpcaccess.googleapis.com",
    "cloudscheduler.googleapis.com",
    "compute.googleapis.com",
    "servicenetworking.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}

# =============================================================================
# SERVICE ACCOUNT FOR CLOUD RUN
# =============================================================================

resource "google_service_account" "cloud_run" {
  account_id   = "nba-analytics-runner"
  display_name = "NBA Analytics Cloud Run Service Account"
  description  = "Service account for NBA Analytics Cloud Run services"
}

# Grant Cloud SQL Client role
resource "google_project_iam_member" "cloud_run_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# Grant Secret Manager accessor role
resource "google_project_iam_member" "cloud_run_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.cloud_run.email}"
}

# =============================================================================
# ARTIFACT REGISTRY
# =============================================================================

resource "google_artifact_registry_repository" "nba_analytics" {
  location      = var.region
  repository_id = "nba-analytics"
  format        = "DOCKER"
  description   = "Container images for NBA Analytics Platform"

  labels = var.labels

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# NETWORKING MODULE
# =============================================================================

module "networking" {
  source = "./modules/networking"

  project_id         = var.project_id
  region             = var.region
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  vpc_connector_cidr = var.vpc_connector_cidr
  labels             = var.labels

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# DATABASE MODULE (CLOUD SQL)
# =============================================================================

module "database" {
  source = "./modules/database"

  project_id          = var.project_id
  region              = var.region
  environment         = var.environment
  db_tier             = var.db_tier
  db_name             = var.db_name
  db_user             = var.db_user
  deletion_protection = var.db_deletion_protection
  vpc_id              = module.networking.vpc_id
  private_vpc_connection = module.networking.private_vpc_connection
  labels              = var.labels

  depends_on = [
    google_project_service.required_apis,
    module.networking
  ]
}

# =============================================================================
# CACHE MODULE (MEMORYSTORE REDIS)
# =============================================================================

module "cache" {
  source = "./modules/cache"

  project_id     = var.project_id
  region         = var.region
  environment    = var.environment
  memory_size_gb = var.redis_memory_size_gb
  tier           = var.redis_tier
  vpc_id         = module.networking.vpc_id
  labels         = var.labels

  depends_on = [
    google_project_service.required_apis,
    module.networking
  ]
}

# =============================================================================
# STORAGE MODULE (GCS FOR ML MODELS)
# =============================================================================

module "storage" {
  source = "./modules/storage"

  project_id           = var.project_id
  region               = var.region
  environment          = var.environment
  cloud_run_sa_email   = google_service_account.cloud_run.email
  labels               = var.labels

  depends_on = [google_project_service.required_apis]
}

# =============================================================================
# CLOUD RUN MODULE
# =============================================================================

module "cloud_run" {
  source = "./modules/cloud_run"

  project_id                  = var.project_id
  region                      = var.region
  environment                 = var.environment
  vpc_connector_id            = module.networking.vpc_connector_id
  service_account_email       = google_service_account.cloud_run.email
  db_connection_name          = module.database.connection_name
  db_name                     = var.db_name
  db_user                     = var.db_user
  db_password_secret_id       = module.database.password_secret_id
  redis_host                  = module.cache.redis_host
  redis_port                  = module.cache.redis_port
  model_bucket_name           = module.storage.bucket_name
  artifact_registry_url       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.nba_analytics.repository_id}"

  # API configuration
  api_cpu            = var.api_cpu
  api_memory         = var.api_memory
  api_min_instances  = var.api_min_instances
  api_max_instances  = var.api_max_instances

  # Dashboard configuration
  dashboard_cpu            = var.frontend_cpu
  dashboard_memory         = var.frontend_memory
  dashboard_min_instances  = var.frontend_min_instances
  dashboard_max_instances  = var.frontend_max_instances

  labels = var.labels

  depends_on = [
    google_project_service.required_apis,
    module.networking,
    module.database,
    module.cache,
    module.storage
  ]
}

# =============================================================================
# SCHEDULER MODULE (DATA INGESTION)
# =============================================================================

module "scheduler" {
  source = "./modules/scheduler"

  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  ingestion_job_name    = module.cloud_run.ingestion_job_name
  service_account_email = google_service_account.cloud_run.email

  depends_on = [
    google_project_service.required_apis,
    module.cloud_run
  ]
}
