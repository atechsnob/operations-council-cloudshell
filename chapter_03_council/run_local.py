"""
chapter_03_council/run_local.py

Local test runner for the Operations Council.

Runs all six sample tickets through the Steward and prints results.
No Cloud Run, no Docker — just your local Python environment + the Gemini API.

Usage:
    python chapter_03_council/run_local.py
    python chapter_03_council/run_local.py --ticket T-1001
    python chapter_03_council/run_local.py --ticket T-megaticket-001 --verbose
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

# Make the repo root importable so this script can be run directly:
#   python chapter_03_council/run_local.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

from chapter_03_council.steward import steward

console = Console()

DATA_FILE = Path(__file__).parent.parent / "data" / "sample_tickets.json"


def load_tickets(ticket_id: str | None = None) -> list[dict]:
    with open(DATA_FILE) as f:
        tickets = json.load(f)["tickets"]
    if ticket_id:
        tickets = [t for t in tickets if t["ticket_id"] == ticket_id]
        if not tickets:
            console.print(f"[red]Ticket {ticket_id} not found in {DATA_FILE}[/red]")
            sys.exit(1)
    return tickets


async def process_ticket(
    runner: InMemoryRunner,
    session_service: InMemorySessionService,
    ticket: dict,
    verbose: bool = False,
) -> str:
    session = await session_service.create_session(
        app_name="operations-council",
        user_id=ticket["ticket_id"],
    )

    message = f"Ticket ID: {ticket['ticket_id']}\nSubject: {ticket['subject']}\n\n{ticket['body']}"

    result_parts = []
    async for event in runner.run_async(
        user_id=ticket["ticket_id"],
        session_id=session.id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message)],
        ),
    ):
        if verbose and event.content:
            for part in event.content.parts:
                if part.text and not event.is_final_response():
                    console.print(f"[dim]  ↳ intermediate: {part.text[:120]}…[/dim]")
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    result_parts.append(part.text)

    return "\n".join(result_parts)


async def main(ticket_id: str | None = None, verbose: bool = False) -> None:
    tickets = load_tickets(ticket_id)
    runner = InMemoryRunner(agent=steward, app_name="operations-council")
    session_service = runner.session_service

    console.print(
        Panel(
            f"[bold cyan]The Operations Council[/bold cyan]\n"
            f"Processing {len(tickets)} ticket(s)",
            expand=False,
        )
    )

    total_start = time.perf_counter()

    for ticket in tickets:
        console.rule(f"[bold]{ticket['ticket_id']}[/bold] — {ticket['subject']}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=console,
        ) as progress:
            task = progress.add_task("Council deliberating…", total=None)
            start = time.perf_counter()
            result = await process_ticket(runner, session_service, ticket, verbose)
            elapsed = time.perf_counter() - start
            progress.update(task, description=f"Done in {elapsed:.1f}s")

        console.print(result)
        console.print(f"\n[dim]  Processed in {elapsed:.1f}s[/dim]\n")

    total = time.perf_counter() - total_start
    console.print(
        Panel(
            f"[green]✓ All {len(tickets)} ticket(s) processed in {total:.1f}s[/green]",
            expand=False,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Operations Council locally")
    parser.add_argument("--ticket", help="Process a single ticket by ID")
    parser.add_argument("--verbose", action="store_true", help="Show intermediate agent steps")
    args = parser.parse_args()

    asyncio.run(main(ticket_id=args.ticket, verbose=args.verbose))
