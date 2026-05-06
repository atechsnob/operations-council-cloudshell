"""
chapter_02_agent_studio/single_agent_triage.py

A single-agent Triage Scout built entirely in Python — the same logic you'd
wire up using the no-code Agent Studio UI, translated into ADK code.

This chapter exists to show the BEFORE state: one agent doing everything.
By the end of Chapter 3 you'll split this into four specialists. The
contrast is the lesson.

Run:
    python chapter_02_agent_studio/single_agent_triage.py
"""

import asyncio
import os
from dotenv import load_dotenv

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()

PROJECT_ID = os.environ["PROJECT_ID"]
REGION = os.environ.get("REGION", "us-central1")
MODEL = os.environ.get("MODEL_FLASH", "gemini-2.0-flash")

# ─── system prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a helpful customer support agent for ContosoCloud, a B2B cloud
infrastructure provider.

When a customer submits a support ticket you will:

1. Classify the ticket into ONE of these categories:
   - PASSWORD_RESET
   - BILLING_DISPUTE
   - OUTAGE_REPORT
   - QUOTA_ISSUE
   - PERMISSIONS_REQUEST
   - ESCALATION_NEEDED
   - DATA_EXPORT
   - OTHER

2. Assess the priority:
   - CRITICAL  — customer is blocked; financial or legal urgency
   - HIGH       — significant impact, needs same-day response
   - MEDIUM     — notable but not blocking
   - LOW        — informational or minor

3. Draft a first-response email to the customer acknowledging receipt,
   confirming the category, and giving an expected resolution timeframe
   based on priority.

Always be professional, concise, and empathetic. If a ticket involves
multiple issues, classify by the highest-priority issue and note the others.
"""

# ─── agent definition ─────────────────────────────────────────────────────────

triage_agent = LlmAgent(
    model=MODEL,
    name="TriageScout_v1",
    description="Single-agent helpdesk triage — classifies tickets and drafts first responses",
    instruction=SYSTEM_PROMPT,
)

# ─── runner ───────────────────────────────────────────────────────────────────

SAMPLE_TICKETS = [
    {
        "ticket_id": "T-1001",
        "subject": "Can't log in",
        "body": "I can't log in to my account this morning. I tried my usual password and it's not working.",
    },
    {
        "ticket_id": "T-megaticket-001",
        "subject": "Multi-issue: cancellation, refund, and a current outage",
        "body": (
            "Three things. (1) We cancelled our contract on Feb 10 but were still charged $4,200 in March — "
            "we want a refund. (2) Our remaining production workloads are seeing intermittent timeouts to "
            "Cloud Storage in us-central1. (3) Please send instructions on exporting our remaining data. "
            "Time-sensitive — board update in 48 hours."
        ),
    },
]


async def run_single_agent() -> None:
    session_service = InMemorySessionService()
    runner = InMemoryRunner(agent=triage_agent, session_service=session_service)

    for ticket in SAMPLE_TICKETS:
        print(f"\n{'='*60}")
        print(f"TICKET {ticket['ticket_id']}: {ticket['subject']}")
        print("=" * 60)

        message = f"Subject: {ticket['subject']}\n\n{ticket['body']}"

        session = await session_service.create_session(
            app_name="TriageScout_v1",
            user_id=ticket["ticket_id"],
        )

        response_parts = []
        async for event in runner.run_async(
            user_id=ticket["ticket_id"],
            session_id=session.id,
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=message)],
            ),
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if part.text:
                        response_parts.append(part.text)

        print("\n".join(response_parts))


# ─── reflection prompt ────────────────────────────────────────────────────────

REFLECTION = """
─────────────────────────────────────────────────────────────
  What you just saw — and why we're replacing it in Ch. 3
─────────────────────────────────────────────────────────────

One agent handled everything: classification, KB lookup (implicit),
response drafting, and priority assessment. That works for simple
tickets but breaks down when:

  • The KB is large and needs dedicated vector search (the Loremaster)
  • Response drafting needs tone/compliance review (the Envoy)
  • Multi-issue tickets need routing logic (the Steward)
  • You want independent evals for each capability

In Chapter 3 we split this into four specialists and wire them into
a graph-based agent network — the Operations Council.
─────────────────────────────────────────────────────────────
"""


if __name__ == "__main__":
    print(REFLECTION)
    asyncio.run(run_single_agent())
    print(REFLECTION)
