"""
chapter_04_memory_and_mcp/run_with_mcp.py

Runs the Operations Council with the MCP CRM server connected.
The Steward gains two new capabilities:
  1. Look up a ticket's history before processing (via MCP)
  2. Write a status update after processing (via MCP)

Prerequisites:
  Start the MCP server in another terminal first:
    python chapter_04_memory_and_mcp/mcp_server.py

Then run this script:
    python chapter_04_memory_and_mcp/run_with_mcp.py
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import AgentTool
from google.adk.tools.mcp_tool import MCPToolset, StdioServerParameters
from google.genai import types as genai_types

sys.path.insert(0, str(Path(__file__).parent.parent))
from chapter_03_council.config import MODEL_PRO
from chapter_03_council.envoy import envoy
from chapter_03_council.loremaster import loremaster
from chapter_03_council.triage_scout import triage_scout

load_dotenv()

MCP_SERVER_SCRIPT = str(Path(__file__).parent / "mcp_server.py")


async def build_steward_with_mcp() -> LlmAgent:
    """Build the Steward agent with MCP CRM tools attached."""

    mcp_toolset = MCPToolset(
        connection_params=StdioServerParameters(
            command="python",
            args=[MCP_SERVER_SCRIPT],
        )
    )

    crm_tools = await mcp_toolset.load_tools()
    print(f"MCP tools loaded: {[t.name for t in crm_tools]}")

    steward_with_mcp = LlmAgent(
        model=MODEL_PRO,
        name="Steward",
        description="Coordinator agent with CRM integration via MCP",
        instruction="""You are the Steward of the Operations Council.

Before processing any ticket, call `get_ticket_history` to check for prior
interactions with this customer. If there is relevant history (previous disputes,
open escalations, stated preferences), include that context when you call the
Loremaster and Envoy.

After generating the draft response, call `update_ticket_status` to record:
  - status: IN_PROGRESS (if human review needed) or RESOLVED (if auto-resolvable)
  - note: one-sentence summary of the action taken

Then follow the standard Steward workflow:
  1. Triage Scout → classification JSON
  2. Loremaster → KB articles
  3. Envoy → draft response
  4. Synthesize and return the structured result

Always call `update_ticket_status` at the end — this closes the loop with the CRM.
""",
        tools=[
            AgentTool(agent=triage_scout),
            AgentTool(agent=loremaster),
            AgentTool(agent=envoy),
            *crm_tools,
        ],
    )

    return steward_with_mcp


async def main() -> None:
    print("Building Steward with MCP CRM integration…")
    steward = await build_steward_with_mcp()

    session_service = InMemorySessionService()
    runner = InMemoryRunner(agent=steward, session_service=session_service)

    # Run the megaticket — the richest test for CRM history lookup
    ticket = {
        "ticket_id": "T-megaticket-001",
        "subject": "Multi-issue: cancellation, refund, and a current outage",
        "body": (
            "Three things. (1) We cancelled our contract on Feb 10 but were still charged "
            "$4,200 in March — we want a refund. (2) Our remaining production workloads are "
            "seeing intermittent timeouts to Cloud Storage in us-central1. (3) Please send "
            "instructions on exporting our remaining data. Board update in 48 hours."
        ),
    }

    session = await session_service.create_session(
        app_name="operations-council",
        user_id=ticket["ticket_id"],
    )

    message = f"Ticket ID: {ticket['ticket_id']}\nSubject: {ticket['subject']}\n\n{ticket['body']}"

    print(f"\n{'='*60}")
    print(f"TICKET {ticket['ticket_id']}: {ticket['subject']}")
    print("=" * 60)

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
                    print(part.text)


if __name__ == "__main__":
    asyncio.run(main())
