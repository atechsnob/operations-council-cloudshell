# Chapter 2 — First Strike: Your First Agent in Agent Studio

## Quest brief

Every Council member starts as a solo operative before joining the guild. In this chapter you'll build the **Triage Scout** as a single agent — first by clicking through Agent Studio's no-code interface, then by exporting that same logic into Python. When you're done, you'll understand the gap between "it works in the UI" and "it works in production code." That gap is what Chapters 3–7 close.

**Plain English:** This chapter is your "hello world" for ADK. Build one agent that reads a ticket, classifies it, and writes a first response. The goal is momentum, not perfection.

---

## Option A — Agent Studio (no-code, click-through)

1. Open [Agent Studio](https://console.cloud.google.com/vertex-ai/agents) in your GCP project
2. Click **Create agent**
3. Fill in:
   - **Name:** `triage-scout-prototype`
   - **Model:** `gemini-2.5-flash`
   - **System instruction:** paste the `SYSTEM_PROMPT` from `single_agent_triage.py`
4. In the **Test** panel, paste one of the sample tickets from `data/sample_tickets.json`
5. Observe the response — classification, priority, and first-response draft
6. When you're satisfied, click **Export → Python (ADK)**

The exported code will look similar to `single_agent_triage.py`.

> **Note:** Agent Studio's export feature was announced at Next '26. If it isn't available in your region yet, skip directly to Option B.

---

## Option B — Run the Python version directly

```bash
source .env
python chapter_02_agent_studio/single_agent_triage.py
```

Expected output for `T-1001` (password reset):

```
TICKET T-1001: Can't log in
============================================================
**Category:** PASSWORD_RESET
**Priority:** MEDIUM

Dear customer,

Thank you for reaching out to ContosoCloud Support. We've received your
ticket and can confirm this is a password reset request ...
```

---

## What's happening under the hood

```
User message → LlmAgent (Gemini Flash) → streamed response
```

`InMemoryRunner` drives the agent locally — no Cloud Run, no network calls except to the Gemini API. `InMemorySessionService` gives each ticket its own isolated conversation history.

The reflection block at the end of the script explains *why* one agent isn't enough for the Megaticket. Read it before moving on.

---

## Exercises

1. Change `MODEL_FLASH` in your `.env` to `gemini-2.5-flash` and rerun — do the classifications change?
2. Add a fourth sample ticket with two simultaneous issues (billing + outage). How does the single agent handle priority?
3. Look at the Megaticket response. Which issues did it miss or combine?

---

## Checkpoint

- [ ] Agent responds to T-1001 with `PASSWORD_RESET` / `MEDIUM`
- [ ] Megaticket response notes all three issues (billing, outage, data export)
- [ ] You've read the reflection block and can explain why multi-agent is better here

---

**Next:** [Chapter 3 — Forging the Specialists: The Operations Council](../chapter_03_council/README.md)
