# Chapter 8 — Council Adjourned: What's Next

## Quest complete

The Operations Council is deployed. The Megaticket is resolved. The governance chamber is sealed. You've built something that didn't exist six chapters ago: a four-agent system that classifies, retrieves, drafts, coordinates, governs itself, and deploys with a CI/CD pipeline that won't let bad code through.

Here's what you actually built, stripped of the narrative:

| Chapter | What you built | Why it matters |
|---|---|---|
| 1 | Environment and data scaffolding | Everything else depends on this being right |
| 2 | Single-agent prototype | Establishes the baseline — and its limits |
| 3 | Four-agent graph network (ADK) | The core architecture pattern |
| 4 | MCP CRM integration + Memory Bank | Agents connected to real systems, not just Gemini |
| 5 | Eval suite + pytest regression guards | Quality gates — agents you can trust and improve |
| 6 | Agent Identity + Gateway + Model Armor | Enterprise trust layer — audit trail, auth, safety |
| 7 | Dockerfile + Cloud Build + Cloud Run | Deployable, scalable, CI/CD-gated production service |

---

## A note on your results

If you're reading this, you've run the course from start to finish. Along the way you probably noticed:

- **Chapter 5:** Some pytest tests failed. The Triage Scout returned JSON wrapped in markdown fences, or a CRITICAL ticket didn't include the exact text "HUMAN REVIEW REQUIRED."
- **Chapter 7:** The Final Trial's automatic assertions caught 4 out of 5 — maybe the model wrote "billing discrepancy" instead of "refund."

**This is normal. This is the lesson.**

LLMs are non-deterministic. The same prompt, same model, same input can produce subtly different outputs on every run. The Council *understood* every issue and *addressed* every concern — but it didn't always use the exact words your assertions expected.

### What this teaches you about production evaluation

| Approach | Brittle? | When to use |
|---|---|---|
| Exact keyword match (`"refund" in output`) | Yes | Quick smoke tests; never as the only eval |
| Fuzzy / stemmed matching (`refund*`, `billing*`) | Less | Better for keyword coverage checks |
| Semantic similarity (embedding distance) | No | When you care about meaning, not wording |
| LLM-as-judge (a second model scores the response) | No | Gold standard for open-ended quality |
| Structured output (JSON schema enforcement) | No | When you can constrain the model's format |

The eval suite in Chapter 5 intentionally uses the simplest approach — exact matching — so you experience the brittleness firsthand. In production, you'd layer these approaches: structured output for classification fields, semantic similarity for response quality, and LLM-as-judge for nuanced requirements like tone and compliance.

**The fact that your Council handled the Megaticket correctly despite a keyword assertion miss is proof that the agent works. The assertion miss is proof that your eval needs to evolve.** That tension — between agent capability and eval reliability — is the central challenge of production AI systems.

---

## The pattern you now own

```
Prototype → Specialists → Memory/Tools → Evals → Governance → Deploy
```

This pattern is reusable. The next time someone asks you to build an agent system — for procurement, for compliance review, for document analysis — you have a template:

1. Start with a single agent (Chapter 2 pattern)
2. Identify the capabilities that deserve specialization (Chapter 3)
3. Connect to external systems via MCP; add persistent memory where needed (Chapter 4)
4. Define a golden eval set *before* you think you're done (Chapter 5)
5. Add identity, registry, and gateway before the first production request (Chapter 6)
6. Deploy behind CI — evals gate the pipeline (Chapter 7)

---

## What to explore next

### On the Gemini Enterprise Agent Platform

**Agent Garden** — Pre-built agent templates (invoice processing, financial analysis, customer 360). Start here if you're building a new agent for a known enterprise workflow. Available in the Agent Studio console.

**Agent Optimizer** — Automated prompt tuning against your eval datasets. Once you have a golden eval set (Chapter 5 pattern), the Optimizer can improve your agents' accuracy without manual prompt iteration.

**Agent Simulation** — Synthetic load testing for multi-agent pipelines. Generates thousands of synthetic tickets from your data schema and runs them through your Council to find edge cases before production.

**BigQuery Graph (Agent Platform)** — For the Loremaster, if your knowledge base has relationships (article A references article B, which has prerequisites C and D), BigQuery Graph gives you richer retrieval than pure vector similarity. Worth exploring for enterprise knowledge bases.

### On multi-agent patterns

**A2A (Agent-to-Agent) protocol** — The emerging standard for agents from *different systems* to collaborate. If you ever need to connect a Gemini agent to an agent built on another framework, A2A is the handshake. Watch the ADK release notes.

**Agent Mesh** — Multiple independent Councils serving different business units, with a meta-coordinator that routes tickets to the right Council. Natural next step after this course.

### On production operations

**Cost management** — Cloud Monitoring has pre-built dashboards for Gemini API spend. Set a budget alert before you scale to real production traffic. The `--max-instances` flag on Cloud Run is your first line of defence.

**Prompt versioning** — As you improve the agents, version your system prompts alongside your code. A changed system prompt is a code change — treat it as one. Tag each agent's identity with its prompt version so audit logs can correlate.

**Model updates** — When new Gemini model versions ship, run your full eval suite against the new model before promoting to production. The eval suite from Chapter 5 is exactly the right vehicle for this.

---

## The course in one sentence

You built a production-ready multi-agent helpdesk system on Google Cloud — from single prototype to deployed, governed, tested service — and you know how to rebuild it for any enterprise workflow.

---

## Thank you

Thank you for building alongside me. If you have questions, feedback, or want to share what you built on top of this — find the course discussion forum on LinkedIn Learning or connect with me directly.

The Council is adjourned. Go build something remarkable.

---

*Course: The Operations Council — Build a Production-Ready Multi-Agent System on Google Cloud*
*Platform: LinkedIn Learning*
*Instructor: Mark Johnson*
*Tools: Gemini Enterprise Agent Platform, ADK, BigQuery, Cloud Run, Cloud Build, MCP*
