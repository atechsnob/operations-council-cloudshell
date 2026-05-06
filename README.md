# The Operations Council — Cloud Shell Edition

> Hands-on code for the LinkedIn Learning course **"The Operations Council: Build a Production-Ready Multi-Agent System on Google Cloud"** — packaged to run entirely inside Google Cloud Shell. No local Python, Docker, or gcloud install required.

---

## Quick start (3 commands)

In Cloud Shell, after cloning this repo:

```bash
bash cloudshell_bootstrap.sh
source ~/.venv/operations-council/bin/activate && set -a && source .env && set +a
python chapter_03_council/run_local.py
```

Or open the interactive walkthrough with the Cloud Shell tutorial sidebar:

```bash
cloudshell launch-tutorial cloudshell_tutorial.md
```

---

## "Open in Cloud Shell" button (for instructors)

Once this repo is published to GitHub, students can launch it with one click:

```markdown
[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://shell.cloud.google.com/cloudshell/editor?cloudshell_git_repo=https://github.com/atechsnob/operations-council-cloudshell&cloudshell_tutorial=cloudshell_tutorial.md)
```

The `.cloudshell/open.json` config in this repo activates the tutorial automatically.

---

## What this builds

A multi-agent council that processes incoming helpdesk tickets:

```
┌─────────────────────────────────────────────────────────────┐
│                      THE STEWARD                            │
│              (Coordinator, gemini-2.0-pro)                  │
│  Receives ticket → Decides who acts → Delegates → Synthesizes│
└──────────┬──────────────────┬──────────────────┬────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
   TRIAGE SCOUT         LOREMASTER             ENVOY
  (Classifier)        (RAG retrieval)     (Response draft)
  gemini-2.0-flash    gemini-2.0-pro      gemini-2.0-pro
                            │
                            ▼
                  ┌──────────────────┐
                  │ Knowledge Base   │
                  │ BigQuery + Vector│
                  └──────────────────┘
```

By Chapter 7, this council is deployed on Cloud Run, governed by Agent Identity and Agent Gateway, validated by an eval suite, and observable end to end.

---

## Why a Cloud Shell version?

| Concern | Local | Cloud Shell |
|---|---|---|
| Install gcloud / Python / Docker | Required | Pre-installed |
| Authenticate to GCP | `gcloud auth login` flow | Already authenticated as you |
| Run Cloud Build | Possible | First-class |
| Run uvicorn + browse via Web Preview | Need local port-forward | Built-in toolbar button |
| Cost | Free | Free (50 hr/week of Cloud Shell, plus normal GCP charges for APIs you call) |
| Persistence | Your machine | 5 GB Cloud Shell home dir |

For a LinkedIn Learning audience, Cloud Shell removes the biggest friction: "I tried to follow along but my Python install is broken."

---

## Chapter map

| Chapter | What you build | Time |
|---|---|---|
| 1. Welcome | Bootstrap, verify environment | 5 min |
| 2. First Strike | Single-agent prototype (the "before") | 5 min |
| 3. Forging the Specialists | Four-agent Council in ADK + local runner | 15 min |
| 4. Memory and the Map | MCP CRM server + Memory Bank wiring | 10 min |
| 5. Trial by Fire | Eval datasets + pytest suite + scorer | 10 min |
| 6. The Governance Chamber | Agent Identity + Registry + Gateway + Model Armor | 10 min |
| 7. The Final Trial | Cloud Build CI/CD + Cloud Run + Megaticket | 15 min |
| 8. Council Adjourned | Wrap-up + what's next | 5 min |

---

## What the bootstrap does for you

`cloudshell_bootstrap.sh` is the Cloud Shell replacement for `setup_env.sh`. It:

1. Auto-detects `PROJECT_ID` from your `gcloud config` — no manual export
2. Creates a Python virtualenv at `~/.venv/operations-council` (survives Cloud Shell session restarts thanks to home dir persistence)
3. Installs all course dependencies
4. Generates a `.env` file from your gcloud config
5. Enables 10 Google Cloud APIs
6. Creates the `operations-council-sa` service account with 11 IAM roles
7. Creates the Artifact Registry Docker repo
8. Creates the BigQuery dataset
9. Loads the knowledge base into BigQuery with embeddings

Idempotent — safe to re-run if anything fails.

---

## Cloud Shell tips

- **Persistent home directory:** Your `~/.venv/operations-council/` and `.env` survive across Cloud Shell sessions automatically.
- **Web Preview:** Click the eye icon in the toolbar to preview anything running on port 8080 (use this for `uvicorn` in Chapter 7).
- **Multiple tabs:** Hit the `+` to open a new shell tab for the MCP server in Chapter 4 while keeping the Council runner in the main tab.
- **Editor:** Click the pencil icon to open the Cloud Shell Editor (a full VS Code-in-the-browser) for editing prompts and code.
- **Boost mode:** If a Chapter 7 build runs slowly, click your profile → **Boost mode** for more CPU.

---

## Files unique to this Cloud Shell variant

| File | Purpose |
|---|---|
| `cloudshell_bootstrap.sh` | Replaces `scripts/setup_env.sh` — adds venv + auto-detected project + KB load |
| `cloudshell_tutorial.md` | Interactive walkthrough for the Cloud Shell tutorial sidebar |
| `.cloudshell/open.json` | Auto-activates the tutorial on repo open |
| `README.md` (this file) | Cloud Shell-specific quick start |

Everything else (the agent code, evals, Dockerfile, governance configs) is identical to the local-dev version.

---

## A note on Next '26 product names

This course uses the post-Next '26 (April 2026) Gemini Enterprise Agent Platform branding. Some service names changed:

| Old name (pre-Apr 2026) | New name |
|---|---|
| Vertex AI | Gemini Enterprise Agent Platform |
| Vertex AI Search | Agent Platform Vector Search |
| Vertex AI Agent Engine | Agent Runtime |
| Vertex AI Memory Bank | Agent Memory Bank |

URL paths in `gcloud` and the docs still reference `vertex-ai/` — that's expected.

---

## Cleanup

To avoid ongoing charges after the course:

```bash
gcloud run services delete operations-council --region=us-central1 --quiet
gcloud artifacts repositories delete operations-council-repo --location=us-central1 --quiet
bq rm -r -f -d operations_council
```

The service account, IAM bindings, and enabled APIs cost nothing.

---

## License

Code in this repository is provided for educational use alongside the LinkedIn Learning course. See `LICENSE` for details.
