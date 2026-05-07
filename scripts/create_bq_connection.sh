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

# IAM propagation between cloudresourcemanager and BigQuery ML's permission
# check can lag 60–180 seconds. A fixed sleep is unreliable, so we probe with
# a real embedding query and only return when it succeeds.
DATASET="${BQ_DATASET:-operations_council}"
PROBE_MODEL="${PROJECT_ID}.${DATASET}._conn_readiness_probe"

# Make sure the dataset exists (create_bq_connection.sh is sometimes called
# before the dataset is created).
bq --location="${REGION}" --project_id="${PROJECT_ID}" mk --dataset \
  "${PROJECT_ID}:${DATASET}" 2>/dev/null || true

# Create (or replace) the probe model. CREATE MODEL itself doesn't invoke the
# endpoint, so this typically succeeds immediately after the role binding.
echo "▶ Creating probe model to test connection…"
bq query --use_legacy_sql=false --project_id="${PROJECT_ID}" --location="${REGION}" \
  --quiet \
  "CREATE OR REPLACE MODEL \`${PROBE_MODEL}\`
   REMOTE WITH CONNECTION \`${PROJECT_ID}.${REGION}.${CONNECTION_ID}\`
   OPTIONS (endpoint = 'text-embedding-005')" >/dev/null 2>&1 || true

echo "▶ Probing for BigQuery ML readiness (up to ~3 minutes)…"
attempts=0
max=18    # 18 × 10s = 3 minutes
ready=0
while [[ ${attempts} -lt ${max} ]]; do
  if bq query --use_legacy_sql=false --project_id="${PROJECT_ID}" --location="${REGION}" \
       --quiet --format=none \
       "SELECT ml_generate_embedding_result
        FROM ML.GENERATE_EMBEDDING(
          MODEL \`${PROBE_MODEL}\`,
          (SELECT 'readiness probe' AS content)
        ) LIMIT 1" >/dev/null 2>&1; then
    ready=1
    break
  fi
  attempts=$((attempts + 1))
  echo "  attempt ${attempts}/${max}: IAM not yet visible to BigQuery ML, sleeping 10s…"
  sleep 10
done

# Clean up the probe model regardless of outcome
bq query --use_legacy_sql=false --project_id="${PROJECT_ID}" --location="${REGION}" \
  --quiet \
  "DROP MODEL IF EXISTS \`${PROBE_MODEL}\`" >/dev/null 2>&1 || true

if [[ ${ready} -eq 1 ]]; then
  echo "  ✓ Connection is ready — ML.GENERATE_EMBEDDING calls will succeed"
else
  echo ""
  echo "  ⚠ Connection IAM not visible to BigQuery ML after 3 minutes."
  echo "  This is a slow IAM-propagation case. The grant is in place, just"
  echo "  not yet visible to BigQuery's check. Wait a few more minutes,"
  echo "  then run:"
  echo "    python scripts/load_knowledge_base.py"
  # Don't exit non-zero — bootstrap can continue, KB rows still load.
fi
