#!/usr/bin/env python3
"""
chapter_01_setup/verify_setup.py

Pre-flight check for the Operations Council course.
Run this after setup_env.sh to confirm everything is wired correctly.

Usage:
    python chapter_01_setup/verify_setup.py
"""

import os
import sys
import importlib
from pathlib import Path


# ─── helpers ────────────────────────────────────────────────────────────────

PASS = "  ✅"
FAIL = "  ❌"
WARN = "  ⚠️ "


def ok(msg: str) -> None:
    print(f"{PASS} {msg}")


def fail(msg: str) -> None:
    print(f"{FAIL} {msg}")


def warn(msg: str) -> None:
    print(f"{WARN} {msg}")


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


# ─── checks ─────────────────────────────────────────────────────────────────

def check_env_vars() -> bool:
    section("Environment variables")
    required = ["PROJECT_ID", "REGION", "GOOGLE_GENAI_USE_VERTEXAI"]
    optional = ["PROJECT_NUMBER", "MODEL_PRO", "MODEL_FLASH", "BQ_DATASET"]
    all_ok = True

    for var in required:
        val = os.environ.get(var)
        if val:
            ok(f"{var} = {val}")
        else:
            fail(f"{var} is not set — add it to your .env file")
            all_ok = False

    for var in optional:
        val = os.environ.get(var)
        if val:
            ok(f"{var} = {val}")
        else:
            warn(f"{var} not set (optional but recommended)")

    return all_ok


def check_python_version() -> bool:
    section("Python version")
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 10):
        ok(f"Python {major}.{minor} — good to go")
        return True
    else:
        fail(f"Python {major}.{minor} — course requires 3.10+ (Cloud Shell ships 3.10+)")
        return False


def check_cloud_shell() -> bool:
    section("Cloud Shell environment")
    in_shell = (
        os.environ.get("CLOUD_SHELL") in ("true", "TRUE")
        or bool(os.environ.get("DEVSHELL_PROJECT_ID"))
    )
    if in_shell:
        ok("Running in Cloud Shell")
    else:
        warn("Not detected as Cloud Shell — that's fine, just informational")
    venv = os.environ.get("VIRTUAL_ENV")
    if venv and "operations-council" in venv:
        ok(f"Virtualenv active: {venv}")
    elif venv:
        warn(f"Virtualenv active but unexpected: {venv}")
    else:
        warn("No virtualenv active. Run: source ~/.venv/operations-council/bin/activate")
    return True


def check_packages() -> bool:
    section("Required packages")
    packages = {
        "google.adk": "google-adk",
        "google.cloud.aiplatform": "google-cloud-aiplatform",
        "google.genai": "google-genai",
        "google.cloud.bigquery": "google-cloud-bigquery",
        "mcp": "mcp",
        "fastapi": "fastapi",
        "pytest": "pytest",
        "dotenv": "python-dotenv",
        "rich": "rich",
        "pydantic": "pydantic",
    }
    all_ok = True
    for module, package in packages.items():
        try:
            importlib.import_module(module)
            ok(f"{package}")
        except ImportError:
            fail(f"{package} — run: pip install {package}")
            all_ok = False
    return all_ok


def check_gcloud() -> bool:
    section("gcloud CLI")
    import shutil
    import subprocess

    # The Python venv can narrow PATH so that gcloud isn't found via
    # subprocess even though it's installed.  Try shutil.which first,
    # then fall back to well-known Cloud Shell / system locations.
    gcloud_bin = shutil.which("gcloud")
    if not gcloud_bin:
        for candidate in [
            Path.home() / "google-cloud-sdk" / "bin" / "gcloud",
            Path("/usr/lib/google-cloud-sdk/bin/gcloud"),
            Path("/usr/bin/gcloud"),
            Path("/snap/bin/gcloud"),
        ]:
            if candidate.exists():
                gcloud_bin = str(candidate)
                break

    if not gcloud_bin:
        fail("gcloud CLI not found — install from https://cloud.google.com/sdk")
        return False

    result = subprocess.run(
        [gcloud_bin, "version", "--format=value(Google Cloud SDK)"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        ok(f"gcloud SDK found: {result.stdout.strip()[:60]}")
    else:
        fail("gcloud CLI found but 'gcloud version' failed")
        return False

    auth = subprocess.run(
        [gcloud_bin, "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"],
        capture_output=True,
        text=True,
    )
    if auth.stdout.strip():
        ok(f"Authenticated as: {auth.stdout.strip()}")
    else:
        fail("No active gcloud account — run: gcloud auth login")
        return False

    return True


def check_bigquery() -> bool:
    section("BigQuery connectivity")
    project = os.environ.get("PROJECT_ID")
    if not project:
        warn("PROJECT_ID not set — skipping BigQuery check")
        return True

    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=project)
        datasets = list(client.list_datasets(max_results=1))
        ok(f"BigQuery API reachable for project {project}")
        return True
    except Exception as exc:
        fail(f"BigQuery check failed: {exc}")
        print("      → Make sure the BigQuery API is enabled and you're authenticated")
        return False


def check_vertex_ai() -> bool:
    section("Gemini Enterprise Agent Platform (Vertex AI) connectivity")
    project = os.environ.get("PROJECT_ID")
    region = os.environ.get("REGION", "us-central1")
    if not project:
        warn("PROJECT_ID not set — skipping Vertex AI check")
        return True

    try:
        import google.cloud.aiplatform as aip

        aip.init(project=project, location=region)
        ok(f"Vertex AI / Agent Platform SDK initialised ({region})")
        return True
    except Exception as exc:
        fail(f"Vertex AI check failed: {exc}")
        print("      → Make sure the AI Platform API is enabled")
        return False


def check_data_files() -> bool:
    section("Course data files")
    repo_root = Path(__file__).parent.parent
    expected = [
        "data/sample_tickets.json",
        "data/knowledge_base/kb_001_password_reset.md",
        "data/knowledge_base/kb_002_billing_dispute.md",
        "data/knowledge_base/kb_003_outage.md",
        "data/knowledge_base/kb_004_quota.md",
        "data/knowledge_base/kb_005_permissions.md",
        "data/knowledge_base/kb_006_escalation.md",
        "data/knowledge_base/kb_007_cost_controls.md",
        "data/knowledge_base/kb_008_data_export.md",
        "scripts/setup_env.sh",
        "scripts/load_knowledge_base.py",
    ]
    all_ok = True
    for path in expected:
        full = repo_root / path
        if full.exists():
            ok(str(path))
        else:
            fail(f"{path} missing")
            all_ok = False
    return all_ok


# ─── main ────────────────────────────────────────────────────────────────────

def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()

    print("\n" + "=" * 50)
    print("  The Operations Council — Environment Check")
    print("=" * 50)

    results = [
        check_python_version(),
        check_cloud_shell(),
        check_env_vars(),
        check_packages(),
        check_gcloud(),
        check_bigquery(),
        check_vertex_ai(),
        check_data_files(),
    ]

    print("\n" + "=" * 50)
    if all(results):
        print("  ✅  All checks passed — you're ready to start!")
    else:
        failed = sum(1 for r in results if not r)
        print(f"  ❌  {failed} check(s) failed — resolve the issues above before continuing")
        sys.exit(1)
    print("=" * 50 + "\n")


if __name__ == "__main__":
    main()
