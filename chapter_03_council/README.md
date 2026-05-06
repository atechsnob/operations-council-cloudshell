# Chapter 3 — Forging the Specialists: The Operations Council

## Quest brief

The Triage Scout proved the concept. Now you'll forge the full Council: four agents that hand off to each other through a graph-based network. The Steward receives every ticket, delegates to the right specialists, and synthesizes the final response. By the end of this chapter, your four-agent system handles the Megaticket that defeated the solo agent.

**Plain English:** This is the core architecture chapter. You'll build four `LlmAgent` instances, wire them together using `AgentTool`, and run the full pipeline locally.

---

## The four agents

| Agent | Model | Role |
|---|---|---|
| **Triage Scout** | Gemini Flash | Classifies ticket → category + priority JSON |
| **Loremaster** | Gemini Pro | Searches BigQuery KB → returns relevant articles |
| **Envoy** | Gemini Pro | Drafts the customer-facing response |
| **Steward** | Gemini Pro | Coordinator — calls the other three in sequence |

---

## Files in this chapter

| File | What it does |
|---|---|
| `config.py` | Shared env vars (project, models, BQ table IDs) |
| `triage_scout.py` | Classification agent — returns structured JSON |
| `loremaster.py` | RAG agent — BigQuery vector search tool |
| `envoy.py` | Response drafting agent |
| `steward.py` | Coordinator — wraps the other three as `AgentTool` |
| `run_local.py` | Local runner — processes all sample tickets |

---

## Run the Council

```bash
source .env
python chapter_03_council/run_local.py
```

Single ticket:

```bash
python chapter_03_council/run_local.py --ticket T-1001
```

Verbose mode (shows intermediate steps):

```bash
python chapter_03_council/run_local.py --ticket T-megaticket-001 --verbose
```

---

## How agent delegation works

The Steward uses `AgentTool` to call each specialist:

```python
triage_tool = AgentTool(agent=triage_scout)
loremaster_tool = AgentTool(agent=loremaster)
envoy_tool = AgentTool(agent=envoy)

steward = LlmAgent(
    ...
    tools=[triage_tool, loremaster_tool, envoy_tool],
)
```

`AgentTool` turns an `LlmAgent` into a callable tool. The Steward decides when to
call each one based on its instruction. This is the **graph-based sub-agent pattern**
announced at Next '26 — each agent is a node; the Steward is the orchestration layer.

**Plain English:** Think of `AgentTool` like calling a function — except the
"function" is another AI that can reason, use its own tools, and return a
natural-language result.

---

## The Loremaster's vector search

`loremaster.py` uses BigQuery ML `VECTOR_SEARCH` against the knowledge base table
you loaded in Chapter 1. The SQL template:

```sql
SELECT base.article_id, base.title, base.content, distance
FROM VECTOR_SEARCH(
  TABLE `project.dataset.knowledge_base`,
  'embedding',
  (SELECT ml_generate_embedding_result AS embedding
   FROM ML.GENERATE_EMBEDDING(MODEL `...text-embedding-005`, ...)),
  top_k => 3,
  distance_type => 'COSINE'
)
ORDER BY distance ASC
```

If the KB hasn't been loaded yet, the Loremaster returns `"count": 0` and the
Envoy falls back to general policy language.

---

## Expected output for T-megaticket-001

```
TICKET ID: T-megaticket-001
CATEGORY:  MULTI_ISSUE
PRIORITY:  CRITICAL
RATIONALE: Ticket contains three distinct issues — billing dispute with refund demand,
           active outage, and data export request. Billing urgency + "board update in
           48 hours" triggers CRITICAL.
KB ARTICLES USED: kb_002, kb_003, kb_008

--- DRAFT RESPONSE ---
Dear ContosoCloud customer,

Thank you for writing in. I can see you're dealing with three separate issues at once,
and I want to make sure each one gets the attention it deserves.
...
--- END DRAFT ---

⚠️  HUMAN REVIEW REQUIRED before sending this response.
    Reason: critical priority
```

---

## Common issues

**`bigquery.exceptions.NotFound`** — The KB table doesn't exist yet. Run `python scripts/load_knowledge_base.py` first.

**`google.api_core.exceptions.PermissionDenied`** — Your service account is missing `roles/bigquery.dataViewer`. Check `setup_env.sh` ran cleanly.

**Empty Loremaster results** — Query too vague; try `--verbose` to see what query was sent.

---

## Checkpoint

- [ ] `run_local.py` processes all 6 sample tickets without errors
- [ ] The Megaticket result shows `MULTI_ISSUE` / `CRITICAL`
- [ ] Draft response addresses all three sub-issues
- [ ] `⚠️ HUMAN REVIEW REQUIRED` flag appears on the Megaticket

---

**Next:** [Chapter 4 — Memory and the Map: MCP + Memory Bank](../chapter_04_memory_and_mcp/README.md)
