# Terraform Backend Configuration
# NBA Analytics Platform - GCP Infrastructure
#
# IMPORTANT: Before running terraform init, create the GCS bucket:
# gsutil mb -p YOUR_PROJECT_ID -l us-central1 gs://YOUR_PROJECT_ID-terraform-state
# gsutil versioning set on gs://YOUR_PROJECT_ID-terraform-state

terraform {
  backend "gcs" {
    # Bucket name will be provided during terraform init
    # terraform init -backend-config="bucket=YOUR_PROJECT_ID-terraform-state"
    prefix = "nba-analytics/state"
  }
}

# To use local backend during development, comment out the above and uncomment:
# terraform {
#   backend "local" {
#     path = "terraform.tfstate"
#   }
# }
