"""
chapter_03_council/config.py

Shared configuration for all four Council agents.
Loaded once at import time; agents reference these constants directly.
"""

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID: str = os.environ["PROJECT_ID"]
REGION: str = os.environ.get("REGION", "us-central1")

MODEL_PRO: str = os.environ.get("MODEL_PRO", "gemini-2.0-pro")
MODEL_FLASH: str = os.environ.get("MODEL_FLASH", "gemini-2.0-flash")

BQ_DATASET: str = os.environ.get("BQ_DATASET", "operations_council")
BQ_KB_TABLE: str = os.environ.get("BQ_KB_TABLE", "knowledge_base")

# Fully-qualified BigQuery table reference
BQ_KB_TABLE_ID: str = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_KB_TABLE}"

# App name used for session scoping across all agents
APP_NAME: str = "operations-council"
