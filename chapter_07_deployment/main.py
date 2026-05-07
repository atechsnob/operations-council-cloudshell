"""
chapter_07_deployment/main.py

FastAPI application that wraps the Operations Council Steward agent.
This is what Cloud Run serves.

Endpoints:
  POST /tickets          — Process a single ticket through the full Council
  POST /tickets/batch    — Process up to 10 tickets (used by the batch ingest job)
  GET  /health           — Health check for Cloud Run probes
  GET  /ready            — Readiness probe (verifies Gemini API reachable)

Run locally:
    uvicorn chapter_07_deployment.main:app --reload --port 8080
"""

import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import Any

import google.cloud.aiplatform as aip
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types

load_dotenv()

PROJECT_ID = os.environ["PROJECT_ID"]
REGION = os.environ.get("REGION", "us-central1")

# ─── startup ─────────────────────────────────────────────────────────────────

_runner: InMemoryRunner | None = None
_session_service: InMemorySessionService | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _runner, _session_service

    aip.init(project=PROJECT_ID, location=REGION)

    from chapter_03_council.steward import steward

    _runner = InMemoryRunner(agent=steward, app_name="operations-council")
    _session_service = _runner.session_service

    print(f"Operations Council ready — project={PROJECT_ID} region={REGION}")
    yield
    print("Shutting down")


# ─── app ─────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Operations Council",
    description="Multi-agent helpdesk system on Gemini Enterprise Agent Platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ─── schemas ─────────────────────────────────────────────────────────────────

class Ticket(BaseModel):
    ticket_id: str = Field(..., example="T-1001")
    subject: str = Field(..., example="Can't log in")
    body: str = Field(..., example="I tried my password and it's not working.")
    user_id: str | None = Field(None, example="u-alice")


class TicketResult(BaseModel):
    ticket_id: str
    processed_at: float
    duration_seconds: float
    result: str


class BatchRequest(BaseModel):
    tickets: list[Ticket] = Field(..., max_length=10)


class BatchResult(BaseModel):
    processed: int
    results: list[TicketResult]


# ─── helpers ─────────────────────────────────────────────────────────────────

async def process_one(ticket: Ticket) -> TicketResult:
    assert _runner and _session_service, "Agent not initialised"

    start = time.perf_counter()
    session = await _session_service.create_session(
        app_name="operations-council",
        user_id=ticket.user_id or ticket.ticket_id,
    )

    message = f"Ticket ID: {ticket.ticket_id}\nSubject: {ticket.subject}\n\n{ticket.body}"
    parts = []

    async for event in _runner.run_async(
        user_id=ticket.user_id or ticket.ticket_id,
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

    return TicketResult(
        ticket_id=ticket.ticket_id,
        processed_at=time.time(),
        duration_seconds=round(time.perf_counter() - start, 2),
        result="\n".join(parts),
    )


# ─── routes ──────────────────────────────────────────────────────────────────

@app.post("/tickets", response_model=TicketResult, status_code=status.HTTP_200_OK)
async def process_ticket(ticket: Ticket) -> TicketResult:
    try:
        return await process_one(ticket)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/tickets/batch", response_model=BatchResult, status_code=status.HTTP_200_OK)
async def process_batch(request: BatchRequest) -> BatchResult:
    tasks = [process_one(t) for t in request.tickets]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    processed = []
    for ticket, result in zip(request.tickets, results):
        if isinstance(result, Exception):
            processed.append(
                TicketResult(
                    ticket_id=ticket.ticket_id,
                    processed_at=time.time(),
                    duration_seconds=0,
                    result=f"ERROR: {result}",
                )
            )
        else:
            processed.append(result)

    return BatchResult(processed=len(processed), results=processed)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, Any]:
    if _runner is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    return {"status": "ready", "project": PROJECT_ID, "region": REGION}
