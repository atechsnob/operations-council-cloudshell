# Chapter 7 — The Final Trial: Production Deployment

## Quest brief

The Council has been tested in the training grounds. Now it's time to deploy it to the world. In this chapter you containerize the Steward, run the eval suite as a deployment gate in Cloud Build, push the image to Artifact Registry, deploy to Cloud Run, and run the Megaticket through the live production endpoint. When `megaticket_scenario.py` exits with all assertions green, the Council has passed the Final Trial.

**Plain English:** This chapter packages the agent as a Docker container, builds a CI/CD pipeline that won't deploy if tests fail, and deploys the whole thing to a managed cloud service (Cloud Run) that auto-scales, handles auth, and gives you logs without managing servers.

---

## Files in this chapter

| File | What it does |
|---|---|
| `Dockerfile` | Container definition — Python 3.12 + uvicorn + FastAPI |
| `cloudbuild.yaml` | CI/CD pipeline — test → build → push → deploy |
| `deploy.sh` | One-command deploy with confirmation prompt |
| `main.py` | FastAPI app wrapping the Steward agent |
| `megaticket_scenario.py` | Capstone script — sends Megaticket to production endpoint |

---

## Architecture: what Cloud Run gets

```
Internet / ticket ingest system
          │
          ▼
   Agent Gateway         ← Chapter 6: auth + rate limiting + Model Armor
          │
          ▼
   Cloud Run service      ← This chapter
   "operations-council"
   ┌──────────────────┐
   │ FastAPI (main.py)│
   │  POST /tickets   │
   │  POST /tickets/batch
   │  GET  /health    │
   │  GET  /ready     │
   └────────┬─────────┘
            │
            ▼
       Steward (ADK)     ← Chapter 3: multi-agent pipeline
```

---

## Step 1 — Test locally inside Cloud Shell

Before deploying, run the FastAPI app in Cloud Shell and preview it via the browser:

```bash
uvicorn chapter_07_deployment.main:app --host 0.0.0.0 --port 8080
```

Now click the **Web Preview** button in the Cloud Shell toolbar (top-right, eye icon) → **Preview on port 8080**. A new browser tab opens with FastAPI's auto-generated docs at `/docs` — you can submit tickets interactively there.

Or test from a second Cloud Shell tab:

```bash
source ~/.venv/operations-council/bin/activate
set -a && source .env && set +a
curl -X POST http://localhost:8080/tickets \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"T-local","subject":"Test","body":"Can you help with a password reset?"}'
```

When you're done, hit `Ctrl+C` in the uvicorn tab.

---

## Step 2 — Deploy via Cloud Build

```bash
source .env
./chapter_07_deployment/deploy.sh
```

The pipeline runs 4 steps:

| Step | What happens |
|---|---|
| **test** | `pytest test_council.py -k "not integration"` — unit + regression guards |
| **build** | `docker build` → image tagged with `$SHORT_SHA` |
| **push** | Push to Artifact Registry |
| **deploy** | `gcloud run deploy` — no public access, service account auth |

**Important:** If any pytest test fails, the build stops at Step 1 and Cloud Run is untouched. This is your deployment gate — evals as CI.

---

## Step 3 — Run the Final Trial

Once deployed:

```bash
source .env
python chapter_07_deployment/megaticket_scenario.py
```

The script:
1. Finds your Cloud Run service URL automatically
2. Gets a fresh identity token via `gcloud auth print-identity-token`
3. POSTs the Megaticket to `/tickets`
4. Prints the full Council response
5. Runs 5 assertions (refund, storage/timeout, export, human-review flag, CRITICAL priority)
6. Exits 0 if all pass, exits 1 if any fail

---

## Cloud Run configuration

The deployment sets these key options:

| Setting | Value | Reason |
|---|---|---|
| `--memory=2Gi` | 2 GB | ADK + multiple Gemini sessions |
| `--cpu=2` | 2 vCPU | Concurrent async requests |
| `--concurrency=10` | 10 | Each request uses ~200MB peak |
| `--min-instances=1` | 1 | Avoid cold start on first ticket |
| `--no-allow-unauthenticated` | — | Agent Gateway handles auth |

---

## Blue-green / traffic splitting (optional extension)

Cloud Run supports traffic splitting by revision tag. After your first deploy:

```bash
# Deploy a canary revision
gcloud run deploy operations-council \
  --image=...council:new-sha \
  --tag=canary \
  --no-traffic \
  --region=$REGION

# Send 10% to canary
gcloud run services update-traffic operations-council \
  --to-tags=canary=10,latest=90 \
  --region=$REGION

# Promote canary to 100% after validation
gcloud run services update-traffic operations-council \
  --to-latest \
  --region=$REGION
```

---

## Exercises

1. Add a `/tickets/batch` test in `megaticket_scenario.py` that sends all 6 sample tickets at once. What's the total latency vs. sequential?
2. Look at Cloud Trace in the GCP console after running the Megaticket. How many spans does the Steward produce?
3. Change `--min-instances=1` to `--min-instances=0` and redeploy. What happens to the first request after 5 minutes of inactivity?

---

## Checkpoint

- [ ] `uvicorn chapter_07_deployment.main:app` starts locally
- [ ] `curl /health` returns `{"status": "ok"}`
- [ ] `deploy.sh` completes without error
- [ ] Cloud Run service appears in `gcloud run services list`
- [ ] `megaticket_scenario.py` exits with all 5 assertions green

---

**Next:** [Chapter 8 — Council Adjourned: What's Next](../chapter_08_wrap_up/README.md)
