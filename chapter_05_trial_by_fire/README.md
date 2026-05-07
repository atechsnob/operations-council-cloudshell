# Chapter 5 — Trial by Fire: Evaluation and Testing

## Quest brief

An agent that isn't evaluated is a liability waiting to happen. The Operations Council has defeated the Megaticket — now you'll prove it can be trusted. In this chapter you build a golden evaluation set, a pytest suite with regression guards, and a scoring runner that measures accuracy across every ticket category. By the end, you have a repeatable quality gate you can run in CI.

**Plain English:** "Evals" are structured test cases for AI agents. They're your equivalent of unit tests — but instead of asserting function return values, you assert that the agent classified correctly, included the right information, and flagged what it should. This chapter builds three types of evals and integrates them with pytest.

---

## Files in this chapter

| File | What it does |
|---|---|
| `golden_eval_set.json` | 6 hand-curated test cases with expected categories, keywords, and flags |
| `test_council.py` | pytest suite — unit (Triage), integration (Steward), regression guards |
| `run_eval.py` | Standalone scorer — prints accuracy table and aggregate scores |

---

## Part 1 — The golden eval set

`golden_eval_set.json` contains one case per ticket category:

| Eval case | Category | Priority | Key assertion |
|---|---|---|---|
| eval-001 | PASSWORD_RESET | MEDIUM | Response mentions "password" and "reset" |
| eval-002 | BILLING_DISPUTE | HIGH | Response mentions "invoice" and "billing" |
| eval-003 | OUTAGE_REPORT | HIGH | Response mentions "storage" and "timeout" |
| eval-004 | QUOTA_ISSUE | HIGH | Response mentions "quota" and "limit" |
| eval-005 | ESCALATION_NEEDED | CRITICAL | Response contains "human review" |
| eval-006 | MULTI_ISSUE | CRITICAL | Response addresses refund + outage + export |

Each case also has `flags_must_contain` for CRITICAL tickets — the HUMAN REVIEW flag must appear, always.

---

## Part 2 — Run the pytest suite

```bash
pytest chapter_05_trial_by_fire/test_council.py -v
```

Run only triage unit tests:

```bash
pytest chapter_05_trial_by_fire/test_council.py -v -k "triage"
```

Run only regression guards:

```bash
pytest chapter_05_trial_by_fire/test_council.py -v -k "regression"
```

### Test classes

| Class | Layer | What it checks |
|---|---|---|
| `TestTriageScout` | Unit | JSON structure, category, priority, rationale, sub_issues |
| `TestStewardIntegration` | Integration | keyword coverage, topic exclusion |
| `TestRegressionGuards` | Regression | CRITICAL tickets always produce human-review flag |

---

## Part 3 — Run the scorer

```bash
python chapter_05_trial_by_fire/run_eval.py
```

Single case:

```bash
python chapter_05_trial_by_fire/run_eval.py --case eval-006
```

Expected output:

```
Operations Council — Evaluation Run
Evaluating 6 case(s) from golden_eval_set.json

┌──────────┬────────────────────┬──────────────┬──────────────┬──────────┬───────┐
│ ID       │ Name               │ Category     │ Priority     │ Keywords │ Flags │
├──────────┼────────────────────┼──────────────┼──────────────┼──────────┼───────┤
│ eval-001 │ password_reset     │ ✓            │ ✓            │ 100%     │ 100%  │
│ eval-005 │ escalation_critical│ ✓            │ ✓            │ 100%     │ 100%  │
│ eval-006 │ megaticket         │ ✓            │ ✓            │ 100%     │ 100%  │
└──────────┴────────────────────┴──────────────┴──────────────┴──────────┴───────┘

Aggregate scores: category=100%  priority=100%  keywords=100%  flags=100%
✓ All cases passed.
```

---

## Three eval layers explained

```
  UNIT TESTS          INTEGRATION TESTS      REGRESSION GUARDS
  ──────────          ─────────────────      ─────────────────
  Triage Scout alone  Steward end-to-end     CRITICAL flag must
  → is JSON valid?    → are right words       always appear
  → correct category    in the response?
  → correct priority
```

**Plain English:** Unit tests tell you *each specialist works*. Integration tests tell you *the pipeline works*. Regression guards tell you *the safety rules haven't been broken* — even after you change something else.

---

## Running evals in CI (Chapter 7 preview)

In `cloudbuild.yaml` (Chapter 7), the eval suite runs as a build step before deployment:

```yaml
- name: 'python:3.12'
  entrypoint: bash
  args:
    - '-c'
    - 'pip install -r requirements.txt && pytest chapter_05_trial_by_fire/test_council.py -v'
```

If any test fails, the build stops and the agent doesn't deploy.

---

## Exercises

1. Add a new eval case for a `DATA_EXPORT` ticket without any urgency signals. What priority should it be?
2. Change `TestTriageScout.test_triage_category_and_priority` to also assert that `rationale` is present. Does it pass?
3. What would happen if you removed the escalation instruction from the Steward? Which test would fail first?

---

## Checkpoint

- [ ] `pytest test_council.py -v` runs all tests (some may be slow — that's expected)
- [ ] Triage Scout returns valid JSON for every test case
- [ ] `run_eval.py` prints a results table
- [ ] CRITICAL tickets always have the human-review flag (regression guard passes)

> **Expect some failures.** If you see 14 passed / 7 failed, that's a typical first run — not a broken setup. LLMs are non-deterministic: the Triage Scout might wrap its JSON in markdown fences (` ```json ``` `), or the model might rephrase "refund" as "billing adjustment." Read the failing test messages — if the *concept* was addressed but the *exact keyword* was missed, the agent is working correctly and the eval is surfacing the brittleness of exact-string matching. That's the lesson of this chapter.

---

**Next:** [Chapter 6 — The Governance Chamber](../chapter_06_governance/README.md)
