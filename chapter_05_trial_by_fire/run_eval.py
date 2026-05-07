"""
chapter_05_trial_by_fire/run_eval.py

Standalone evaluation runner that scores the Operations Council against the
golden eval set and prints a human-readable report.

Unlike pytest (which is pass/fail), this script measures:
  - Category accuracy  (exact match on expected_triage.category)
  - Priority accuracy  (exact match on expected_triage.priority)
  - Keyword coverage   (% of response_must_contain terms present)
  - Flag compliance    (% of required flags present)

Run:
    python chapter_05_trial_by_fire/run_eval.py
    python chapter_05_trial_by_fire/run_eval.py --case eval-006
"""

import argparse
import asyncio
import json
import re
import sys
from pathlib import Path

# Make the repo root importable so this script can be run directly:
#   python chapter_05_trial_by_fire/run_eval.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rich.console import Console
from rich.table import Table

from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

from chapter_03_council.steward import steward
from chapter_03_council.triage_scout import triage_scout

console = Console()
EVAL_SET_PATH = Path(__file__).parent / "golden_eval_set.json"


def load_cases(case_id: str | None = None) -> list[dict]:
    with open(EVAL_SET_PATH) as f:
        cases = json.load(f)["cases"]
    if case_id:
        cases = [c for c in cases if c["id"] == case_id]
    return cases


async def run_agent_async(agent, message: str) -> str:
    runner = InMemoryRunner(agent=agent, app_name="eval")
    session_service = runner.session_service
    session = await session_service.create_session(app_name="eval", user_id="eval-user")

    parts = []
    async for event in runner.run_async(
        user_id="eval-user",
        session_id=session.id,
        new_message=genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=message)],
        ),
    ):
        if event.is_final_response() and event.content:
            for part in event.content.parts:
                if part.text:
                    parts.append(part.text)
    return "\n".join(parts)


def extract_triage_from_steward_output(output: str) -> dict:
    """Pull CATEGORY and PRIORITY from the Steward's structured output."""
    category_match = re.search(r"CATEGORY:\s*(\w+)", output, re.IGNORECASE)
    priority_match = re.search(r"PRIORITY:\s*(\w+)", output, re.IGNORECASE)
    return {
        "category": category_match.group(1).upper() if category_match else "UNKNOWN",
        "priority": priority_match.group(1).upper() if priority_match else "UNKNOWN",
    }


def score_case(case: dict, output: str) -> dict:
    triage = extract_triage_from_steward_output(output)
    expected = case.get("expected_triage", {})

    category_correct = triage["category"] == expected.get("category", "")
    priority_correct = triage["priority"] == expected.get("priority", "")

    must_contain = case.get("response_must_contain", [])
    must_not_contain = case.get("response_must_not_contain", [])
    flags_required = case.get("flags_must_contain", [])

    keyword_hits = [kw for kw in must_contain if kw.lower() in output.lower()]
    keyword_misses = [kw for kw in must_contain if kw.lower() not in output.lower()]
    bad_keywords = [kw for kw in must_not_contain if kw.lower() in output.lower()]
    flag_hits = [f for f in flags_required if f.upper() in output.upper()]
    flag_misses = [f for f in flags_required if f.upper() not in output.upper()]

    keyword_score = len(keyword_hits) / max(len(must_contain), 1)
    flag_score = len(flag_hits) / max(len(flags_required), 1)

    return {
        "id": case["id"],
        "name": case["name"],
        "category_correct": category_correct,
        "priority_correct": priority_correct,
        "got_category": triage["category"],
        "got_priority": triage["priority"],
        "expected_category": expected.get("category", ""),
        "expected_priority": expected.get("priority", ""),
        "keyword_score": keyword_score,
        "keyword_misses": keyword_misses,
        "bad_keywords": bad_keywords,
        "flag_score": flag_score,
        "flag_misses": flag_misses,
    }


async def main(case_id: str | None = None) -> None:
    cases = load_cases(case_id)
    console.print(f"\n[bold cyan]Operations Council — Evaluation Run[/bold cyan]")
    console.print(f"Evaluating {len(cases)} case(s) from {EVAL_SET_PATH.name}\n")

    results = []
    for case in cases:
        console.print(f"[dim]Running {case['id']}: {case['name']}…[/dim]")
        output = await run_agent_async(steward, case["input"])
        score = score_case(case, output)
        results.append(score)

    # ── Summary table ──────────────────────────────────────────────────────────
    table = Table(title="Eval Results", show_lines=True)
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Category", justify="center")
    table.add_column("Priority", justify="center")
    table.add_column("Keywords", justify="center")
    table.add_column("Flags", justify="center")

    for r in results:
        cat = "[green]✓[/green]" if r["category_correct"] else f"[red]✗ ({r['got_category']})[/red]"
        pri = "[green]✓[/green]" if r["priority_correct"] else f"[red]✗ ({r['got_priority']})[/red]"
        kw = f"[green]{r['keyword_score']:.0%}[/green]" if r["keyword_score"] == 1.0 else f"[yellow]{r['keyword_score']:.0%}[/yellow]"
        fl = f"[green]{r['flag_score']:.0%}[/green]" if r["flag_score"] == 1.0 else f"[red]{r['flag_score']:.0%}[/red]"
        table.add_row(r["id"], r["name"], cat, pri, kw, fl)

    console.print(table)

    # ── Aggregate scores ───────────────────────────────────────────────────────
    cat_acc = sum(r["category_correct"] for r in results) / len(results)
    pri_acc = sum(r["priority_correct"] for r in results) / len(results)
    kw_avg = sum(r["keyword_score"] for r in results) / len(results)
    flag_avg = sum(r["flag_score"] for r in results) / len(results)

    console.print(
        f"\n[bold]Aggregate scores:[/bold] "
        f"category={cat_acc:.0%}  priority={pri_acc:.0%}  "
        f"keywords={kw_avg:.0%}  flags={flag_avg:.0%}"
    )

    # ── Failures detail ────────────────────────────────────────────────────────
    failures = [r for r in results if not r["category_correct"] or r["flag_misses"] or r["bad_keywords"]]
    if failures:
        console.print("\n[red bold]Failures requiring attention:[/red bold]")
        for r in failures:
            if not r["category_correct"]:
                console.print(f"  {r['id']}: category {r['got_category']} ≠ {r['expected_category']}")
            if r["flag_misses"]:
                console.print(f"  {r['id']}: missing flags {r['flag_misses']}")
            if r["bad_keywords"]:
                console.print(f"  {r['id']}: unexpected keywords {r['bad_keywords']}")
    else:
        console.print("\n[green bold]✓ All cases passed.[/green bold]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Operations Council evaluation")
    parser.add_argument("--case", help="Run a single eval case by ID")
    args = parser.parse_args()
    asyncio.run(main(case_id=args.case))
