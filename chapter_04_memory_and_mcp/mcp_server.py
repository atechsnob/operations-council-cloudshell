"""
chapter_04_memory_and_mcp/mcp_server.py

A lightweight MCP (Model Context Protocol) server that simulates a CRM /
ticketing system. The Steward connects to this server to read ticket history
and write status updates — without direct database access.

This server exposes three tools:
  - get_ticket_history: returns past interactions for a given user_id
  - update_ticket_status: writes a status + resolution note to a ticket
  - list_open_tickets: returns all tickets currently in OPEN or IN_PROGRESS state

Run in one terminal:
    python chapter_04_memory_and_mcp/mcp_server.py

Then run the updated Council (chapter_04_memory_and_mcp/run_with_mcp.py) in another.
"""

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# ─── in-memory "CRM" ─────────────────────────────────────────────────────────
# In a real system this would be a database. For the course, a dict is fine.

_TICKETS: dict[str, dict] = {
    "T-1001": {
        "ticket_id": "T-1001",
        "user_id": "u-alice",
        "subject": "Can't log in",
        "status": "OPEN",
        "history": [
            {
                "ts": "2026-03-01T08:12:00Z",
                "actor": "customer",
                "note": "I can't log in this morning.",
            }
        ],
    },
    "T-1002": {
        "ticket_id": "T-1002",
        "user_id": "u-bob",
        "subject": "Charge looks wrong",
        "status": "OPEN",
        "history": [
            {
                "ts": "2026-03-01T09:05:00Z",
                "actor": "customer",
                "note": "March invoice has unexpected $1,247 charge.",
            }
        ],
    },
    "T-1005": {
        "ticket_id": "T-1005",
        "user_id": "u-eve",
        "subject": "Need a refund — urgent",
        "status": "IN_PROGRESS",
        "history": [
            {
                "ts": "2026-03-01T07:30:00Z",
                "actor": "customer",
                "note": "Charged $3,400 for cancelled service. Threatening legal escalation.",
            },
            {
                "ts": "2026-03-01T08:00:00Z",
                "actor": "system",
                "note": "Auto-routed to ESCALATION queue.",
            },
        ],
    },
    "T-megaticket-001": {
        "ticket_id": "T-megaticket-001",
        "user_id": "u-megacorp",
        "subject": "Multi-issue: cancellation, refund, and outage",
        "status": "OPEN",
        "history": [
            {
                "ts": "2026-03-01T06:45:00Z",
                "actor": "customer",
                "note": "Three issues: refund $4,200, intermittent Cloud Storage timeouts, data export instructions needed.",
            }
        ],
    },
}

# ─── MCP server ──────────────────────────────────────────────────────────────

app = Server("contoso-crm")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_ticket_history",
            description="Returns the full history for a ticket_id, including all previous notes and status changes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string", "description": "The ticket ID (e.g. T-1001)"}
                },
                "required": ["ticket_id"],
            },
        ),
        Tool(
            name="update_ticket_status",
            description="Updates a ticket's status and appends a resolution note.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "string"},
                    "status": {
                        "type": "string",
                        "enum": ["OPEN", "IN_PROGRESS", "RESOLVED", "ESCALATED", "CLOSED"],
                    },
                    "note": {"type": "string", "description": "Note to append to the ticket history"},
                },
                "required": ["ticket_id", "status", "note"],
            },
        ),
        Tool(
            name="list_open_tickets",
            description="Returns all tickets with status OPEN or IN_PROGRESS.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_ticket_history":
        ticket_id = arguments["ticket_id"]
        ticket = _TICKETS.get(ticket_id)
        if not ticket:
            return [TextContent(type="text", text=json.dumps({"error": f"Ticket {ticket_id} not found"}))]
        return [TextContent(type="text", text=json.dumps(ticket))]

    elif name == "update_ticket_status":
        ticket_id = arguments["ticket_id"]
        ticket = _TICKETS.get(ticket_id)
        if not ticket:
            return [TextContent(type="text", text=json.dumps({"error": f"Ticket {ticket_id} not found"}))]
        ticket["status"] = arguments["status"]
        ticket["history"].append(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "actor": "operations-council",
                "note": arguments["note"],
            }
        )
        return [TextContent(type="text", text=json.dumps({"updated": ticket_id, "status": arguments["status"]}))]

    elif name == "list_open_tickets":
        open_tickets = [
            {"ticket_id": t["ticket_id"], "subject": t["subject"], "status": t["status"]}
            for t in _TICKETS.values()
            if t["status"] in ("OPEN", "IN_PROGRESS")
        ]
        return [TextContent(type="text", text=json.dumps({"tickets": open_tickets, "count": len(open_tickets)}))]

    return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ─── entry point ─────────────────────────────────────────────────────────────

async def main() -> None:
    print("ContosoCloud CRM MCP server starting on stdio…")
    async with stdio_server() as streams:
        await app.run(streams[0], streams[1], app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
