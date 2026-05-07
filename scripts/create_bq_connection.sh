#!/usr/bin/env bash
# scripts/create_bq_connection.sh
#
# Creates the BigQuery external connection that the Loremaster's embeddings
# table relies on. BigQuery ML's ML.GENERATE_EMBEDDING calls out to the
# Gemini Enterprise Agent Platform embedding endpoint via this connection.
#
# Idempotent — safe to re-run.
#
# Required env (loaded from .env):
#   PROJECT_ID, REGION

set -euo pipefail

CONNECTION_ID="${BQ_CONNECTION_ID:-agent-platform-conn}"

if [[ -z "${PROJECT_ID:-}" ]]; then
  echo "ERROR: PROJECT_ID not set. Source .env first." >&2
  exit 1
fi

REGION="${REGION:-us-central1}"

echo "▶ Ensuring BigQuery connection ${CONNECTION_ID} exists in ${REGION}"

if ! bq show --connection --location="${REGION}" --project_id="${PROJECT_ID}" "${CONNECTION_ID}" &>/dev/null; then
  bq mk --connection \
    --location="${REGION}" \
    --project_id="${PROJECT_ID}" \
    --connection_type=CLOUD_RESOURCE \
    "${CONNECTION_ID}"
  echo "  ✓ Created connection ${CONNECTION_ID}"
else
  echo "  ✓ Connection already exists"
fi

# The connection has its own auto-generated service account that needs
# permission to call the Vertex AI / Agent Platform embedding endpoint.
CONN_SA="$(bq show --connection --format=json \
  --location="${REGION}" --project_id="${PROJECT_ID}" "${CONNECTION_ID}" \
  | python3 -c 'import sys, json; print(json.load(sys.stdin)["cloudResource"]["serviceAccountId"])')"

echo "▶ Connection service account: ${CONN_SA}"
echo "▶ Granting roles/aiplatform.user (with retry for IAM propagation)…"

attempts=0
max=15
until gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${CONN_SA}" \
        --role="roles/aiplatform.user" \
        --condition=None \
        --quiet >/dev/null 2>&1; do
  attempts=$((attempts + 1))
  if [[ ${attempts} -ge ${max} ]]; then
    echo "  ✗ Failed to bind aiplatform.user after ${max} attempts" >&2
    exit 1
  fi
  sleep 4
done
echo "  ✓ aiplatform.user granted to connection service account"

# IAM bindings for BigQuery connections take ~30–60s to fully propagate
# before BigQuery ML jobs can use them. Don't fail if a caller runs
# load_knowledge_base.py too quickly — they can re-run.
echo "▶ Waiting 30s for IAM propagation before BigQuery ML calls succeed…"
sleep 30
echo "  ✓ Connection ready for ML.GENERATE_EMBEDDING calls"
