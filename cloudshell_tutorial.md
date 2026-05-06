# The Operations Council — Cloud Shell Tutorial

## Welcome

This interactive tutorial walks you through building a four-agent helpdesk system on the Gemini Enterprise Agent Platform. Everything runs inside Cloud Shell — no local setup required.

**Estimated time:** 60–90 minutes for all 8 chapters.

Click **Start** to begin.

## Prerequisites

You need:
- A Google Cloud project with **billing enabled**
- The `roles/owner` or equivalent permissions to create service accounts and enable APIs

Confirm your project is set:

```bash
gcloud config get-value project
```

If it's wrong or unset:

```bash
gcloud config set project YOUR_PROJECT_ID
```

<walkthrough-project-billing-setup></walkthrough-project-billing-setup>

## Chapter 1 — Bootstrap your environment

Run the one-command bootstrap. This enables APIs, creates a service account, sets up Artifact Registry, BigQuery, and a Python venv:

```bash
bash cloudshell_bootstrap.sh
```

This takes 2–4 minutes. While it runs, the script prints each step so you can follow along.

When it's done, activate the venv and load env vars:

```bash
source ~/.venv/operations-council/bin/activate
set -a && source .env && set +a
```

Verify everything works:

```bash
python chapter_01_setup/verify_setup.py
```

You should see ✅ on every check.

## Chapter 2 — Your first agent

Run the single-agent prototype. This is the "before" state — one agent doing all the work:

```bash
python chapter_02_agent_studio/single_agent_triage.py
```

Watch how it handles the **Megaticket** (the multi-issue ticket at the bottom of the run). Notice how the response is competent but flat — no specialist routing, no priority escalation logic, no human-review flag.

That's what we'll fix in Chapter 3.

## Chapter 3 — Build the Council

This is the heart of the course. Four agents wired into a graph:

```bash
python chapter_03_council/run_local.py
```

Run all 6 sample tickets through the Council. Pay attention to:

- **T-1001** (password reset) — simple flow, one specialist call
- **T-1005** (refund + legal threat) — `CRITICAL` priority, human-review flag raised
- **T-megaticket-001** — three sub-issues, all addressed in one response

Try just the Megaticket with verbose output:

```bash
python chapter_03_council/run_local.py --ticket T-megaticket-001 --verbose
```

You'll see the Steward delegating to each specialist in turn.

## Chapter 4 — MCP and Memory

Open a new Cloud Shell tab (`+` icon), then in the new tab:

```bash
source ~/.venv/operations-council/bin/activate
set -a && source .env && set +a
python chapter_04_memory_and_mcp/mcp_server.py
```

Leave that running. Back in your main tab:

```bash
python chapter_04_memory_and_mcp/run_with_mcp.py
```

The Steward now calls the fake CRM before/after processing — read past ticket history, write status updates.

For Memory Bank (mock mode until SDK ships):

```bash
python chapter_04_memory_and_mcp/memory_wiring.py
```

## Chapter 5 — Evals and tests

Run the pytest suite:

```bash
pytest chapter_05_trial_by_fire/test_council.py -v
```

Or the standalone scorer with a results table:

```bash
python chapter_05_trial_by_fire/run_eval.py
```

This is what you'll wire into Cloud Build as a deployment gate in Chapter 7.

## Chapter 6 — Governance

Run the Model Armor demo to see input screening in action:

```bash
python chapter_06_governance/model_armor_demo.py
```

Watch the prompt-injection attempt get blocked, and the PII (email, phone, SSN, credit card) get redacted before reaching Gemini.

Provision agent identities (mock mode until SDK ships):

```bash
python chapter_06_governance/agent_identity.py
```

The YAML configs in this chapter (`registry_config.yaml`, `gateway_config.yaml`) are applied with `gcloud agent-platform` commands. They're declarative — see `chapter_06_governance/README.md` for the apply commands.

## Chapter 7 — Deploy to Cloud Run

First, test the FastAPI app locally inside Cloud Shell. Run it on port 8080:

```bash
uvicorn chapter_07_deployment.main:app --host 0.0.0.0 --port 8080
```

Click **Web Preview** in the Cloud Shell toolbar (top right) → **Preview on port 8080**. Your browser opens the FastAPI auto-docs at `/docs`.

Stop the server (`Ctrl+C`) and deploy via Cloud Build:

```bash
bash chapter_07_deployment/deploy.sh
```

This runs the eval suite, builds the image, pushes to Artifact Registry, and deploys to Cloud Run. Takes 5–8 minutes the first time.

## Chapter 7 (continued) — The Final Trial

Once deployed, send the Megaticket through the production endpoint:

```bash
python chapter_07_deployment/megaticket_scenario.py
```

The script auto-discovers your Cloud Run URL, gets an identity token, and runs 5 assertions. All green = victory.

## Chapter 8 — Council Adjourned

You're done. To review what you built and explore extensions:

```bash
cat chapter_08_wrap_up/README.md
```

## Cleanup (optional)

To avoid ongoing charges, tear down the resources:

```bash
# Delete the Cloud Run service
gcloud run services delete operations-council --region=us-central1 --quiet

# Delete the Artifact Registry repo
gcloud artifacts repositories delete operations-council-repo --location=us-central1 --quiet

# Delete the BigQuery dataset
bq rm -r -f -d operations_council
```

The service account, IAM bindings, and enabled APIs are safe to leave — they cost nothing.

## Congratulations!

<walkthrough-conclusion-trophy></walkthrough-conclusion-trophy>

You've built, tested, governed, and deployed a production-ready multi-agent system on Google Cloud — entirely inside Cloud Shell.

Next, take the pattern you learned and apply it to a real problem in your organization. The Council template works for procurement triage, compliance review, document analysis, internal IT support, and any workflow where specialist roles + a coordinator beats a single generalist agent.
