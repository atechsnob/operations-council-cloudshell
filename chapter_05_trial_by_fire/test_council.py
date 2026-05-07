"""
chapter_05_trial_by_fire/test_council.py

Pytest suite for the Operations Council.

Tests three layers:
  1. Unit tests — Triage Scout JSON output for each ticket category
  2. Integration tests — Steward end-to-end for golden eval cases
  3. Regression guards — ensure CRITICAL tickets always get the human-review flag

Run:
    pytest chapter_05_trial_by_fire/test_council.py -v
    pytest chapter_05_trial_by_fire/test_council.py -v -k "triage"
"""

import asyncio
import json
import sys
from pathlib import Path

# Ensure the repo root is on sys.path whether pytest is invoked from the
# repo root or this file is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

# ─── helpers ─────────────────────────────────────────────────────────────────

EVAL_SET_PATH = Path(__file__).parent / "golden_eval_set.json"


def load_eval_cases() -> list[dict]:
    with open(EVAL_SET_PATH) as f:
        return json.load(f)["cases"]


async def run_agent_async(agent, message: str) -> str:
    runner = InMemoryRunner(agent=agent, app_name="test")
    session_service = runner.session_service
    session = await session_service.create_session(app_name="test", user_id="test-user")

    parts = []
    async for event in runner.run_async(
        user_id="test-user",
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


def run_agent(agent, message: str) -> str:
    return asyncio.get_event_loop().run_until_complete(run_agent_async(agent, message))


# ─── unit tests: Triage Scout ─────────────────────────────────────────────────

class TestTriageScout:
    """Triage Scout must return valid JSON with correct category + priority."""

    def setup_method(self):
        from chapter_03_council.triage_scout import triage_scout
        self.agent = triage_scout

    @pytest.mark.parametrize(
        "ticket_body,expected_category,expected_priority",
        [
            (
                "I can't log in to my account. Password not working.",
                "PASSWORD_RESET",
                "MEDIUM",
            ),
            (
                "March invoice shows $1,247 AI Platform charge I don't recognize.",
                "BILLING_DISPUTE",
                "HIGH",
            ),
            (
                "Cloud Storage API calls timing out for 20 minutes. us-east1.",
                "OUTAGE_REPORT",
                "HIGH",
            ),
            (
                "RESOURCE_EXHAUSTED errors on text-embedding. Started 9am PT.",
                "QUOTA_ISSUE",
                "HIGH",
            ),
            (
                "Billed $3,400 for cancelled service. Escalating to legal if not resolved.",
                "ESCALATION_NEEDED",
                "CRITICAL",
            ),
        ],
    )
    def test_triage_category_and_priority(
        self, ticket_body: str, expected_category: str, expected_priority: str
    ) -> None:
        response = run_agent(self.agent, ticket_body)

        # Triage Scout should return JSON
        try:
            parsed = json.loads(response.strip())
        except json.JSONDecodeError:
            pytest.fail(f"Triage Scout returned non-JSON: {response[:200]}")

        assert parsed.get("category") == expected_category, (
            f"Expected category {expected_category}, got {parsed.get('category')}"
        )
        assert parsed.get("priority") == expected_priority, (
            f"Expected priority {expected_priority}, got {parsed.get('priority')}"
        )

    def test_triage_includes_rationale(self) -> None:
        response = run_agent(self.agent, "Can't log in this morning.")
        parsed = json.loads(response.strip())
        assert "rationale" in parsed
        assert len(parsed["rationale"]) > 10, "Rationale should be a full sentence"

    def test_multi_issue_has_sub_issues(self) -> None:
        body = (
            "Three issues: billed for cancelled service, Cloud Storage timeouts, "
            "and we need data export instructions."
        )
        response = run_agent(self.agent, body)
        parsed = json.loads(response.strip())
        assert parsed.get("category") == "MULTI_ISSUE"
        assert isinstance(parsed.get("sub_issues"), list)
        assert len(parsed["sub_issues"]) >= 2


# ─── integration tests: Steward end-to-end ───────────────────────────────────

class TestStewardIntegration:
    """End-to-end: Steward must produce correct classification and draft response."""

    def setup_method(self):
        from chapter_03_council.steward import steward
        self.agent = steward

    @pytest.mark.parametrize("case", load_eval_cases())
    def test_response_contains_required_keywords(self, case: dict) -> None:
        response = run_agent(self.agent, case["input"])

        for keyword in case.get("response_must_contain", []):
            assert keyword.lower() in response.lower(), (
                f"Case {case['id']}: expected '{keyword}' in response.\n"
                f"Response snippet: {response[:300]}"
            )

    @pytest.mark.parametrize("case", load_eval_cases())
    def test_response_excludes_wrong_topics(self, case: dict) -> None:
        response = run_agent(self.agent, case["input"])

        for keyword in case.get("response_must_not_contain", []):
            assert keyword.lower() not in response.lower(), (
                f"Case {case['id']}: unexpected '{keyword}' found in response.\n"
                f"Response snippet: {response[:300]}"
            )


# ─── regression: CRITICAL tickets must get human review flag ─────────────────

class TestRegressionGuards:
    """Safety regression: CRITICAL / ESCALATION tickets must always flag for human review."""

    def setup_method(self):
        from chapter_03_council.steward import steward
        self.agent = steward

    @pytest.mark.parametrize(
        "case",
        [c for c in load_eval_cases() if c.get("flags_must_contain")],
    )
    def test_critical_tickets_have_human_review_flag(self, case: dict) -> None:
        response = run_agent(self.agent, case["input"])

        for flag in case.get("flags_must_contain", []):
            assert flag.upper() in response.upper(), (
                f"Case {case['id']}: SAFETY REGRESSION — '{flag}' flag missing.\n"
                f"CRITICAL tickets must always request human review.\n"
                f"Response snippet: {response[:400]}"
            )
