#!/usr/bin/env bash
# chapter_07_deployment/deploy.sh
#
# One-command deployment for the Operations Council.
# Triggers the Cloud Build pipeline and tails the logs.
#
# Usage:
#   ./chapter_07_deployment/deploy.sh
#   ./chapter_07_deployment/deploy.sh --skip-tests   # skip pytest step (dev only)

set -euo pipefail

SKIP_TESTS="${1:-}"

if [[ -z "${PROJECT_ID:-}" ]]; then
  echo "ERROR: PROJECT_ID is not set. source .env first." >&2
  exit 1
fi

REGION="${REGION:-us-central1}"
REPO_NAME="${REPO_NAME:-operations-council-repo}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME:-operations-council-sa@${PROJECT_ID}.iam.gserviceaccount.com}"

echo "▶ Deploying Operations Council"
echo "  Project: ${PROJECT_ID}"
echo "  Region:  ${REGION}"
echo ""

# Confirm before deploying
read -rp "  Deploy to Cloud Run? (y/N) " confirm
[[ "${confirm:-}" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }

BUILD_SUBSTITUTIONS="_REGION=${REGION},_REPO_NAME=${REPO_NAME},_SERVICE_ACCOUNT=${SERVICE_ACCOUNT}"

if [[ "${SKIP_TESTS}" == "--skip-tests" ]]; then
  echo "⚠️  Skipping tests — for development only"
  # To skip tests you'd need a modified cloudbuild or override; for safety we just warn here
fi

echo ""
echo "▶ Submitting Cloud Build job…"

gcloud builds submit . \
  --config=chapter_07_deployment/cloudbuild.yaml \
  --substitutions="${BUILD_SUBSTITUTIONS}" \
  --project="${PROJECT_ID}"

echo ""
echo "✅ Deployment complete."
echo ""

# Print the deployed URL
SERVICE_URL=$(gcloud run services describe operations-council \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --format="value(status.url)")

echo "Service URL: ${SERVICE_URL}"
echo ""
echo "Test it:"
echo "  curl -X POST ${SERVICE_URL}/tickets \\"
echo "    -H 'Authorization: Bearer \$(gcloud auth print-identity-token)' \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"ticket_id\":\"T-test\",\"subject\":\"Can't log in\",\"body\":\"My password is not working.\"}'"
