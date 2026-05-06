"""
chapter_03_council/loremaster.py

The Loremaster — knowledge retrieval agent.

Responsibilities:
  1. Receive a ticket category + ticket body from the Steward
  2. Search the BigQuery knowledge base for relevant articles
  3. Return the most relevant article excerpts + their IDs

The Steward passes the Loremaster's findings to the Envoy for response drafting.

VERIFY: The BigQuery vector search function name (`VECTOR_SEARCH`) and
embedding model endpoint were verified against GA BigQuery ML docs (2025-Q4).
If the BigQuery ML embedding model path changes, update EMBEDDING_MODEL below.
"""

import json
import os
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from google.cloud import bigquery

from .config import BQ_KB_TABLE_ID, MODEL_PRO, PROJECT_ID, REGION

EMBEDDING_MODEL = f"projects/{PROJECT_ID}/locations/{REGION}/publishers/google/models/text-embedding-005"

_bq_client: bigquery.Client | None = None


def _get_bq_client() -> bigquery.Client:
    global _bq_client
    if _bq_client is None:
        _bq_client = bigquery.Client(project=PROJECT_ID)
    return _bq_client


def search_knowledge_base(query: str, max_results: int = 3) -> str:
    """Search the ContosoCloud knowledge base for articles relevant to `query`.

    Args:
        query: Natural-language description of what to look for.
        max_results: Maximum number of articles to return (default 3).

    Returns:
        JSON string with a list of matching articles (title, content, article_id).
    """
    client = _get_bq_client()

    sql = f"""
    SELECT
      base.article_id,
      base.title,
      base.content,
      distance
    FROM
      VECTOR_SEARCH(
        TABLE `{BQ_KB_TABLE_ID}`,
        'embedding',
        (
          SELECT ml_generate_embedding_result AS embedding
          FROM ML.GENERATE_EMBEDDING(
            MODEL `{EMBEDDING_MODEL}`,
            (SELECT @query AS content)
          )
        ),
        top_k => @max_results,
        distance_type => 'COSINE'
      )
    ORDER BY distance ASC
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("query", "STRING", query),
            bigquery.ScalarQueryParameter("max_results", "INT64", max_results),
        ]
    )

    try:
        rows = list(client.query(sql, job_config=job_config).result())
        articles = [
            {
                "article_id": row.article_id,
                "title": row.title,
                "content": row.content[:1500],  # truncate for context window budget
                "relevance_distance": round(row.distance, 4),
            }
            for row in rows
        ]
        return json.dumps({"articles": articles, "count": len(articles)})
    except Exception as exc:
        return json.dumps({"error": str(exc), "articles": [], "count": 0})


kb_search_tool = FunctionTool(func=search_knowledge_base)

LOREMASTER_INSTRUCTION = """You are the Loremaster of the Operations Council.

You receive a support ticket category and the ticket body. Your job is to
retrieve the most relevant knowledge base articles that would help a support
agent respond to this ticket accurately.

Steps:
1. Call `search_knowledge_base` with a focused query derived from the ticket body.
   Keep queries under 150 words — the KB is technical, so precise queries work better.
2. If the first search returns low-relevance results (distance > 0.4), try a
   rephrased query using the category as additional context.
3. Return a summary of what you found:
   - Which article IDs are most relevant and why
   - Key steps or policy excerpts from those articles
   - Whether the KB has sufficient coverage to fully answer the ticket

If no relevant articles are found, say so clearly — the Envoy will handle it.
"""

loremaster = LlmAgent(
    model=MODEL_PRO,
    name="Loremaster",
    description=(
        "Searches the ContosoCloud knowledge base and returns relevant article excerpts "
        "for a given ticket category and body."
    ),
    instruction=LOREMASTER_INSTRUCTION,
    tools=[kb_search_tool],
)
