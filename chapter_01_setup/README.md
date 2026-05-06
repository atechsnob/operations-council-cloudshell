# Chapter 1 — Welcome to the Operations Council (Cloud Shell)

## Quest brief

You've been recruited as the Architect of the Council — a guild of four AI agents that will take over your company's helpdesk backlog. Before you can summon the agents, you need to prepare your workspace. In Cloud Shell, that means running one bootstrap script and confirming the environment is ready.

**Plain English:** This chapter is project setup. One script enables the right Google Cloud APIs, creates a service account, builds a Python virtualenv, generates your `.env` file, and loads the knowledge base. The verify script then confirms everything is wired correctly.

---

## Step 1 — Confirm your project

```bash
gcloud config get-value project
```

If the wrong project is shown:

```bash
gcloud config set project YOUR_PROJECT_ID
```

Make sure billing is enabled on the project.

---

## Step 2 — Run the bootstrap

```bash
bash cloudshell_bootstrap.sh
```

This takes 2–4 minutes. It:

- Detects your project from `gcloud config` (no manual `export PROJECT_ID` needed)
- Creates a Python venv at `~/.venv/operations-council`
- Installs all course dependencies into the venv
- Generates a `.env` file from your gcloud config
- Enables 10 Google Cloud APIs
- Creates the `operations-council-sa` service account with required roles
- Creates the Artifact Registry Docker repo
- Creates the BigQuery dataset
- Loads the knowledge base into BigQuery (with embeddings)

The script is idempotent — re-running is safe.

---

## Step 3 — Activate the venv

The bootstrap creates the venv but each new shell tab needs to activate it. Run:

```bash
source ~/.venv/operations-council/bin/activate
set -a && source .env && set +a
```

You can save typing by adding this to `~/.bashrc`:

```bash
echo 'alias council-env="source ~/.venv/operations-council/bin/activate && set -a && source ~/operations-council-cloudshell/.env && set +a"' >> ~/.bashrc
```

Then in any new tab: `council-env`

---

## Step 4 — Verify the environment

```bash
python chapter_01_setup/verify_setup.py
```

Every check should show ✅. The script tests:

- Python 3.10+ (Cloud Shell ships 3.10+; venv may use 3.11 or 3.12)
- All required packages installed
- `gcloud` CLI authenticated
- BigQuery API accessible
- Gemini Enterprise Agent Platform SDK initialized
- All course data files present
- Cloud Shell environment detected

---

## Step 5 — Confirm the knowledge base loaded

```bash
bq query --use_legacy_sql=false --project_id=$PROJECT_ID \
  "SELECT article_id, title FROM \`$PROJECT_ID.operations_council.knowledge_base\` LIMIT 10"
```

You should see 8 article rows. If the table is missing or empty:

```bash
python scripts/load_knowledge_base.py
```

---

## ContosoCloud — the fictional company

All sample data uses a fictional company called **ContosoCloud**, a B2B cloud infrastructure provider. The 8 knowledge base articles cover common helpdesk scenarios: password resets, billing disputes, outages, quota limits, permissions, escalations, cost controls, and data exports.

---

## Cloud Shell quirks worth knowing

- **Session timeout:** Cloud Shell disconnects idle sessions after about 1 hour. Reconnect, run `council-env` (if you set the alias), and continue. Your venv and `.env` persist.
- **Disk quota:** 5 GB. The full venv is ~1 GB. Run `du -sh ~/.venv/operations-council` to check.
- **Boost mode:** If pip install or Cloud Build feels slow, enable Boost in the toolbar profile menu. It gives you more CPU for the rest of the session.

---

## Checkpoint

- [ ] `gcloud config get-value project` shows the right project
- [ ] `cloudshell_bootstrap.sh` finished without errors
- [ ] `python chapter_01_setup/verify_setup.py` shows all ✅
- [ ] `bq query ...` returns 8 KB articles

---

**Next:** [Chapter 2 — First Strike: Your First Agent in Agent Studio](../chapter_02_agent_studio/README.md)
