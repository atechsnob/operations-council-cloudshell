#!/usr/bin/env bash
# scripts/setup_env.sh
#
# One-time setup for the Operations Council course.
# Enables APIs, creates a service account, grants permissions, and
# creates the BigQuery dataset and Artifact Registry repo.
#
# Run from the repo root:
#   export PROJECT_ID="your-gcp-project"
#   export REGION="us-central1"
#   ./scripts/setup_env.sh

set -euo pipefail

if [[ -z "${PROJECT_ID:-}" ]]; then
  echo "ERROR: PROJECT_ID is not set. export PROJECT_ID=your-project first." >&2
  exit 1
fi

REGION="${REGION:-us-central1}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-operations-council-sa}"
SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
REPO_NAME="${REPO_NAME:-operations-council-repo}"
BQ_DATASET="${BQ_DATASET:-operations_council}"

echo "▶ Setting active project to ${PROJECT_ID}"
gcloud config set project "${PROJECT_ID}" --quiet

echo "▶ Enabling required APIs"
gcloud services enable \
  aiplatform.googleapis.com \
  artifactregistry.googleapis.com \
  bigquery.googleapis.com \
  cloudbuild.googleapis.com \
  cloudresourcemanager.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  logging.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  --project="${PROJECT_ID}"

echo "▶ Creating service account ${SA_EMAIL} (idempotent)"
if ! gcloud iam service-accounts describe "${SA_EMAIL}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
    --display-name="Operations Council agent service account" \
    --project="${PROJECT_ID}"
fi

echo "▶ Granting roles to service account"
for role in \
  roles/aiplatform.user \
  roles/artifactregistry.admin \
  roles/bigquery.dataEditor \
  roles/bigquery.jobUser \
  roles/cloudbuild.builds.editor \
  roles/iam.serviceAccountUser \
  roles/logging.logWriter \
  roles/logging.viewer \
  roles/run.admin \
  roles/secretmanager.secretAccessor \
  roles/storage.objectViewer; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${role}" \
    --condition=None \
    --quiet >/dev/null
done

echo "▶ Creating Artifact Registry repository (idempotent)"
if ! gcloud artifacts repositories describe "${REPO_NAME}" \
     --location="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  gcloud artifacts repositories create "${REPO_NAME}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Operations Council agent images" \
    --project="${PROJECT_ID}"
fi

echo "▶ Creating BigQuery dataset (idempotent)"
bq --location="${REGION}" mk --dataset \
  --description="Knowledge base for the Operations Council" \
  "${PROJECT_ID}:${BQ_DATASET}" 2>/dev/null || true

PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"

cat <<EOF

✅ Setup complete.

Add these to your .env file:

  PROJECT_ID="${PROJECT_ID}"
  PROJECT_NUMBER="${PROJECT_NUMBER}"
  REGION="${REGION}"
  SERVICE_ACCOUNT_NAME="${SA_EMAIL}"
  REPO_NAME="${REPO_NAME}"
  BQ_DATASET="${BQ_DATASET}"

Next: run python chapter_01_setup/verify_setup.py
EOF
