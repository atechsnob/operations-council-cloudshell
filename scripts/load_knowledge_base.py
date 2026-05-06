#!/usr/bin/env python3
"""scripts/load_knowledge_base.py

Loads the sample knowledge base from data/knowledge_base/*.md into BigQuery
and creates an embeddings column powered by BigQuery ML for the Loremaster
agent's RAG lookups.

Run after scripts/setup_env.sh:
    python scripts/load_knowledge_base.py

Environment:
    PROJECT_ID, REGION, BQ_DATASET, BQ_KB_TABLE
"""

from __future__ import annotations

import os
import pathlib
import sys
import uuid
from typing import Iterable

from google.cloud import bigquery


PROJECT_ID = os.environ.get("PROJECT_ID")
REGION = os.environ.get("REGION", "us-central1")
DATASET = os.environ.get("BQ_DATASET", "operations_council")
TABLE = os.environ.get("BQ_KB_TABLE", "knowledge_base")
KB_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "knowledge_base"

if not PROJECT_ID:
    sys.exit("ERROR: PROJECT_ID is not set. Source your .env first.")


def parse_kb_file(path: pathlib.Path) -> dict:
    """Parse a knowledge base markdown file with simple frontmatter.

    Frontmatter format (top of file):
        ---
        id: kb-001
        title: Resetting your password
        category: account
        ---
        Body text continues here...
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path.name} missing frontmatter")

    _, frontmatter, body = text.split("---", 2)
    meta = {}
    for line in frontmatter.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()

    return {
        "doc_id": meta.get("id", str(uuid.uuid4())),
        "title": meta.get("title", path.stem),
        "category": meta.get("category", "general"),
        "content": body.strip(),
        "source_file": path.name,
    }


def collect_kb_rows() -> list[dict]:
    if not KB_DIR.exists():
        sys.exit(f"ERROR: knowledge base directory not found: {KB_DIR}")
    rows = [parse_kb_file(p) for p in sorted(KB_DIR.glob("*.md"))]
    if not rows:
        sys.exit(f"ERROR: no .md files found in {KB_DIR}")
    return rows


def create_table(client: bigquery.Client) -> str:
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    schema = [
        bigquery.SchemaField("doc_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("title", "STRING"),
        bigquery.SchemaField("category", "STRING"),
        bigquery.SchemaField("content", "STRING"),
        bigquery.SchemaField("source_file", "STRING"),
    ]
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table, exists_ok=True)
    print(f"▶ Table ready: {table_id}")
    return table_id


def load_rows(client: bigquery.Client, table_id: str, rows: Iterable[dict]) -> None:
    # Replace contents on each load so re-running is idempotent.
    job_config = bigquery.LoadJobConfig(
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )
    rows_list = list(rows)
    job = client.load_table_from_json(rows_list, table_id, job_config=job_config)
    job.result()
    print(f"▶ Loaded {len(rows_list)} knowledge base articles")


def create_embeddings_table(client: bigquery.Client) -> None:
    """Create a sibling table with text embeddings for vector search.

    Uses BigQuery ML's ML.GENERATE_EMBEDDING function with a remote model
    pointing at the embeddings endpoint on Agent Platform.

    VERIFY: The remote model creation syntax may have shifted post Next '26.
    See: https://cloud.google.com/bigquery/docs/generate-text-embedding
    """
    embeddings_table = f"{PROJECT_ID}.{DATASET}.{TABLE}_embeddings"
    remote_model = f"{PROJECT_ID}.{DATASET}.embeddings_model"

    # Step 1: Create the remote embeddings model (idempotent).
    client.query(f"""
        CREATE MODEL IF NOT EXISTS `{remote_model}`
        REMOTE WITH CONNECTION `{PROJECT_ID}.{REGION}.agent-platform-conn`
        OPTIONS (endpoint = 'text-embedding-005')
    """).result()

    # Step 2: Generate embeddings into the sibling table.
    client.query(f"""
        CREATE OR REPLACE TABLE `{embeddings_table}` AS
        SELECT
          doc_id, title, category, content, source_file,
          ml_generate_embedding_result AS embedding
        FROM ML.GENERATE_EMBEDDING(
          MODEL `{remote_model}`,
          (SELECT doc_id, title, category, content, source_file,
                  CONCAT(title, '\\n\\n', content) AS content
             FROM `{PROJECT_ID}.{DATASET}.{TABLE}`)
        )
    """).result()
    print(f"▶ Embeddings table ready: {embeddings_table}")


def main() -> None:
    client = bigquery.Client(project=PROJECT_ID, location=REGION)
    rows = collect_kb_rows()
    table_id = create_table(client)
    load_rows(client, table_id, rows)
    try:
        create_embeddings_table(client)
    except Exception as exc:  # noqa: BLE001
        # Embeddings creation requires a BQ-to-AI Platform connection.
        # We emit a friendly error so learners can come back after Chapter 3
        # when they set the connection up.
        print(f"⚠ Could not create embeddings table: {exc}")
        print("  This is expected if you haven't created the BigQuery <-> Agent Platform")
        print("  connection yet. See chapter_03_council/loremaster/README.md.")


if __name__ == "__main__":
    main()
