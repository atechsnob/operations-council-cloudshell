# Chapter 6 — The Governance Chamber

## Quest brief

A Council without governance is an unsupervised contractor. In this chapter you give the Operations Council a paper trail, an identity, and a gate. Each agent gets a cryptographic identity so audit logs can tell the Steward from the Loremaster. The Agent Registry catalogs every agent's capabilities and endpoints. Agent Gateway enforces who can call the Steward and what content is allowed. Model Armor filters prompt injections before they reach Gemini. By the end, the Council is auditable, governable, and compliant.

**Plain English:** This chapter adds the enterprise trust layer. Think of Agent Identity as each agent's badge, the Registry as the org chart, the Gateway as the security checkpoint at the front door, and Model Armor as the bag scanner.

---

## Files in this chapter

| File | What it does |
|---|---|
| `agent_identity.py` | Provisions cryptographic identities for all four agents |
| `registry_config.yaml` | Agent Registry — metadata catalog for all agents |
| `gateway_config.yaml` | Agent Gateway — auth, rate limits, content policy, routing |
| `model_armor_demo.py` | Demonstrates input screening and PII redaction |

---

## The governance stack

```
Customer Ticket
      │
      ▼
 ┌─────────────────────────────────────────┐
 │         Agent Gateway                   │
 │  • JWT auth (only allowed callers)      │
 │  • Rate limiting (60 req/min)           │
 │  • Routes to Steward endpoint           │
 └──────────────┬──────────────────────────┘
                │
                ▼
 ┌─────────────────────────────────────────┐
 │         Model Armor                     │
 │  • Prompt injection detection           │
 │  • PII redaction                        │
 │  • Topic blocking                       │
 └──────────────┬──────────────────────────┘
                │
                ▼
         The Steward
    (+ Triage Scout, Loremaster, Envoy)
                │
                ▼
 ┌─────────────────────────────────────────┐
 │      Agent Identity + Audit Logs        │
 │  • Each agent call attributed to its    │
 │    cryptographic identity               │
 │  • Full input/output logs to BigQuery   │
 └─────────────────────────────────────────┘
```

---

## Part 1 — Agent Identity

```bash
python chapter_06_governance/agent_identity.py
```

In mock mode (SDK not yet available) this prints the identity resource names that *would* be provisioned. Once the SDK ships, the same code makes real API calls.

**Why agent-level identity matters for compliance:**
Without it, Cloud Audit Logs show `service-account@project.iam.gserviceaccount.com` — you can't tell which of the four agents made a call. With Agent Identity, the log entry says `Loremaster` and includes the attestation token. That's the difference between "an agent called BigQuery" and "the Loremaster called BigQuery at 09:14:03 while processing ticket T-1005."

---

## Part 2 — Agent Registry

The Registry YAML is declarative — one `gcloud` command applies it:

```bash
envsubst < chapter_06_governance/registry_config.yaml | \
  gcloud agent-platform registries apply --config=- --project=$PROJECT_ID
```

> `envsubst` substitutes `${PROJECT_ID}` and `${PROJECT_NUMBER}` from your environment. Requires `gettext` (brew install gettext / apt install gettext).

The Registry stores each agent's version, model, capabilities, and identity reference. Agent Gateway uses this to validate routing rules and capability requirements.

---

## Part 3 — Agent Gateway

Apply the gateway config:

```bash
envsubst < chapter_06_governance/gateway_config.yaml | \
  gcloud agent-platform gateways apply --config=- --project=$PROJECT_ID
```

Once deployed, the Steward is only reachable via the Gateway URL. Direct Cloud Run access is blocked by IAM. This means:
- All tickets go through rate limiting and content filtering
- The only way to bypass Model Armor is to get IAM access to Cloud Run directly (your compliance team's concern, not yours)

---

## Part 4 — Model Armor

```bash
python chapter_06_governance/model_armor_demo.py
```

Three demo cases:
1. Normal ticket with PII → PII redacted before reaching Gemini
2. Prompt injection attempt → blocked at the gate
3. Credit card / SSN in ticket body → redacted

**Why this matters for SLED / federal customers:** Agencies often require that no PII touches the LLM. Model Armor's redaction happens *before* the prompt reaches Gemini, which means the audit trail shows only `[EMAIL REDACTED]` in the model input log — not the actual address.

---

## VERIFY checklist

These four features were announced at Next '26 (April 2026). Before deploying to production:

- [ ] `AgentIdentityServiceClient` — confirm import path in current SDK
- [ ] `ModelArmorServiceClient` — confirm `sanitize_user_prompt` method name
- [ ] Registry YAML — confirm `apiVersion` string against current docs
- [ ] Gateway YAML — confirm `contentPolicy.modelArmor.policyRef` field name

---

## Exercises

1. Add a `PROFANITY` category to the Model Armor local screen. What regex patterns would catch it?
2. What would the audit log entry look like if the Loremaster called BigQuery with Agent Identity attached vs. without?
3. In `gateway_config.yaml`, change `sampleRate` to `0.1`. When would you want 10% sampling vs 100%?

---

## Checkpoint

- [ ] `agent_identity.py` runs without errors (mock mode is fine)
- [ ] `model_armor_demo.py` blocks the injection attempt and redacts PII
- [ ] Registry and Gateway YAMLs have `${PROJECT_ID}` placeholders ready for substitution
- [ ] You can explain the difference between Agent Identity and service account identity

---

**Next:** [Chapter 7 — The Final Trial: Production Deployment](../chapter_07_deployment/README.md)
