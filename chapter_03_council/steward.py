"""
chapter_03_council/steward.py

The Steward — coordinator agent. Orchestrates the other three specialists.

Responsibilities:
  1. Receive an incoming ticket
  2. Call the Triage Scout to classify it
  3. Call the Loremaster with the classification to retrieve KB articles
  4. Call the Envoy with all context to draft the response
  5. Return a structured result: classification + draft response + any flags

VERIFY: The ADK graph-based sub-agent network (`sub_agents` parameter) was
announced at Next '26. Confirm the exact parameter name and delegation
mechanism against current ADK docs before deploying.
"""

from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool

from .config import MODEL_PRO
from .envoy import envoy
from .loremaster import loremaster
from .triage_scout import triage_scout

# Wrap each specialist as a callable tool for the Steward
triage_tool = AgentTool(agent=triage_scout)
loremaster_tool = AgentTool(agent=loremaster)
envoy_tool = AgentTool(agent=envoy)

STEWARD_INSTRUCTION = """You are the Steward of the Operations Council — the coordinator who
orchestrates the three specialist agents to process incoming helpdesk tickets.

## Your workflow

For every ticket you receive, execute these steps IN ORDER:

### Step 1 — Classify with the Triage Scout
Call the `TriageScout` tool with the full ticket body.
Parse the JSON response to extract: category, priority, rationale, sub_issues.

### Step 2 — Retrieve knowledge with the Loremaster
Call the `Loremaster` tool with:
  - The category from Step 1
  - The full ticket body

### Step 3 — Draft the response with the Envoy
Call the `Envoy` tool with:
  - The full ticket body (subject + original text)
  - The triage JSON from Step 1
  - The Loremaster's findings from Step 2

### Step 4 — Synthesize and return

Return a structured summary in this format:

```
TICKET ID: <id if provided, else N/A>
CATEGORY:  <from triage>
PRIORITY:  <from triage>
RATIONALE: <from triage>
KB ARTICLES USED: <article IDs or "none">

--- DRAFT RESPONSE ---
<Envoy's draft>
--- END DRAFT ---

FLAGS: <any items needing human review, or "none">
```

## Escalation gate

If priority is CRITICAL or category is ESCALATION_NEEDED, append:

```
⚠️  HUMAN REVIEW REQUIRED before sending this response.
    Reason: [critical priority | customer threatened legal action | other]
```

## Multi-issue handling

If the Triage Scout returns category MULTI_ISSUE, call the Loremaster once
per sub_issue (up to 3), then pass all findings to the Envoy together.

## Error handling

If any specialist agent returns an error or empty response, note it in FLAGS
and complete the workflow with whatever information is available. Never fail
silently.
"""

steward = LlmAgent(
    model=MODEL_PRO,
    name="Steward",
    description="Coordinator agent — orchestrates Triage Scout, Loremaster, and Envoy to process helpdesk tickets end to end.",
    instruction=STEWARD_INSTRUCTION,
    tools=[triage_tool, loremaster_tool, envoy_tool],
)
