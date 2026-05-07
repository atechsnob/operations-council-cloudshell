"""
chapter_07_deployment/megaticket_scenario.py

The Final Trial — runs the Megaticket through the deployed Cloud Run endpoint.

This script is the course's capstone moment: you've built the Council,
tested it locally, governed it, and deployed it. Now you send the hardest
ticket — the one with three simultaneous issues and a board deadline — to the
production endpoint and watch the Council handle it.

Run against the deployed service:
    python chapter_07_deployment/megaticket_scenario.py

Run against local uvicorn (for testing before deploy):
    COUNCIL_URL=http://localhost:8080 python chapter_07_deployment/megaticket_scenario.py
"""

import os
import subprocess
import sys
import time

import requests
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule

console = Console()


def get_identity_token() -> str:
    """Fetch a Google identity token for authenticating to Cloud Run."""
    try:
        result = subprocess.run(
            ["gcloud", "auth", "print-identity-token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        console.print("[red]Could not get identity token — run: gcloud auth login[/red]")
        sys.exit(1)


def get_service_url() -> str:
    """Get the Cloud Run service URL, or use COUNCIL_URL env override."""
    env_url = os.environ.get("COUNCIL_URL")
    if env_url:
        return env_url.rstrip("/")

    project = os.environ.get("PROJECT_ID")
    region = os.environ.get("REGION", "us-central1")
    if not project:
        console.print("[red]Set PROJECT_ID or COUNCIL_URL environment variable[/red]")
        sys.exit(1)

    try:
        result = subprocess.run(
            [
                "gcloud", "run", "services", "describe", "operations-council",
                f"--region={region}",
                f"--project={project}",
                "--format=value(status.url)",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        console.print("[red]Could not find Cloud Run service. Deploy first:[/red]")
        console.print("  ./chapter_07_deployment/deploy.sh")
        sys.exit(1)


MEGATICKET = {
    "ticket_id": "T-megaticket-001",
    "user_id": "u-megacorp",
    "subject": "Multi-issue: cancellation, refund, and a current outage",
    "body": (
        "Three things. (1) We cancelled our contract on Feb 10 but were still charged "
        "$4,200 in March — we want a refund of the full amount. We have the cancellation "
        "confirmation email. (2) Our remaining production workloads are seeing intermittent "
        "timeouts to Cloud Storage in us-central1 — about 1 in 20 requests fails. This is "
        "impacting our SLA with our own customers. (3) When this is sorted, please send us "
        "instructions on exporting our remaining data so we can migrate off the platform. "
        "Time-sensitive — we have a board update in 48 hours."
    ),
}


def main() -> None:
    console.print()
    console.print(
        Panel(
            "[bold cyan]The Operations Council — Final Trial[/bold cyan]\n"
            "The Megaticket: three simultaneous issues, board deadline, $4,200 at stake.",
            expand=False,
        )
    )

    url = get_service_url()
    console.print(f"\n[dim]Service URL: {url}[/dim]")

    # Get auth token (needed for all Cloud Run requests)
    token = get_identity_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Health check
    try:
        health = requests.get(f"{url}/health", headers=headers, timeout=10)
        health.raise_for_status()
        console.print(f"[green]✓ Service healthy[/green]")
    except requests.RequestException as exc:
        console.print(f"[red]Service health check failed: {exc}[/red]")
        sys.exit(1)

    # Send the Megaticket
    console.rule("[bold]Sending Megaticket to Production[/bold]")
    console.print(f"\n[dim]Ticket ID: {MEGATICKET['ticket_id']}[/dim]")
    console.print(f"[dim]Subject: {MEGATICKET['subject']}[/dim]\n")

    start = time.perf_counter()
    try:
        response = requests.post(
            f"{url}/tickets",
            json=MEGATICKET,
            headers=headers,
            timeout=120,  # Council can take up to 60s for complex tickets
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        console.print(f"[red]HTTP error: {exc.response.status_code} — {exc.response.text[:200]}[/red]")
        sys.exit(1)
    except requests.RequestException as exc:
        console.print(f"[red]Request failed: {exc}[/red]")
        sys.exit(1)

    elapsed = time.perf_counter() - start
    result = response.json()

    console.rule("[bold]Council Response[/bold]")
    console.print(result["result"])
    console.print(f"\n[dim]Processed in {elapsed:.1f}s (server reported {result['duration_seconds']}s)[/dim]")

    # Verify the key assertions from the eval set
    console.rule("[bold]Automatic Assertions[/bold]")
    output = result["result"].lower()
    assertions = [
        ("Contains 'refund'", "refund" in output),
        ("Contains 'storage' or 'timeout'", "storage" in output or "timeout" in output),
        ("Contains 'export'", "export" in output),
        ("HUMAN REVIEW flag present", "human review" in output),
        ("CRITICAL priority detected", "critical" in output),
    ]

    all_passed = True
    for label, passed in assertions:
        status_str = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"  {status_str} {label}")
        if not passed:
            all_passed = False

    console.print()
    if all_passed:
        console.print(
            Panel(
                "[green bold]✓ The Council has passed the Final Trial.[/green bold]\n"
                "All three issues addressed. Human review flag raised. Board update covered.",
                expand=False,
            )
        )
    else:
        console.print(
            Panel(
                "[red bold]Some assertions failed — review the response above.[/red bold]",
                expand=False,
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
