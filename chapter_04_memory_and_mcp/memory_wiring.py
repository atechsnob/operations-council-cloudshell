"""
chapter_04_memory_and_mcp/memory_wiring.py

Demonstrates Agent Memory Bank integration — giving the Council persistent
memory across separate ticket sessions.

Use cases wired here:
  1. User preference memory  — remember that u-alice prefers email over ticket portal
  2. Ticket context memory   — remember that u-megacorp had a billing dispute in Feb
  3. Custom session IDs      — map external CRM ticket IDs to agent session IDs

VERIFY: Memory Bank Python SDK (MemoryBankServiceClient, create_memory,
query_memory_bank) was announced at Next '26. Verify the exact method names
and proto shapes against current google-cloud-aiplatform release notes before
deploying. The pattern below reflects the announced API surface.
"""

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ["PROJECT_ID"]
REGION = os.environ.get("REGION", "us-central1")


# ─── Memory Bank client wrapper ───────────────────────────────────────────────

class AgentMemoryBank:
    """
    Thin wrapper around the Agent Memory Bank API.

    VERIFY: Import path and class name may change as the SDK stabilises.
    Announced API surface: https://cloud.google.com/products/gemini-enterprise-agent-platform
    """

    def __init__(self, memory_bank_id: str | None = None):
        # VERIFY: Confirm the correct import path post-SDK release
        try:
            from google.cloud.aiplatform_v1beta1 import MemoryBankServiceClient  # type: ignore
            self._client = MemoryBankServiceClient()
        except ImportError:
            print(
                "⚠️  MemoryBankServiceClient not yet available in this SDK version.\n"
                "   This file demonstrates the announced API — update when SDK ships."
            )
            self._client = None

        self.memory_bank_id = memory_bank_id or os.environ.get("MEMORY_BANK_ID")
        self.parent = f"projects/{PROJECT_ID}/locations/{REGION}"

    def create_memory_bank(self, display_name: str = "operations-council-memory") -> str:
        """Create a new Memory Bank and return its ID."""
        if not self._client:
            return "mock-memory-bank-id"

        # VERIFY: CreateMemoryBankRequest proto structure
        request = {
            "parent": self.parent,
            "memory_bank": {
                "display_name": display_name,
                "description": "Persistent memory for the Operations Council helpdesk agents",
            },
        }
        response = self._client.create_memory_bank(request=request)
        return response.name.split("/")[-1]

    def store_memory(self, user_id: str, content: str, scope: str = "user") -> None:
        """Store a memory entry for a user.

        Args:
            user_id:  The user or customer this memory belongs to.
            content:  The text to remember.
            scope:    "user" for cross-session user facts, "session" for ephemeral.
        """
        if not self._client or not self.memory_bank_id:
            print(f"[mock] store_memory: user={user_id}, scope={scope}, content={content[:80]}")
            return

        # VERIFY: CreateMemoryRequest proto structure
        request = {
            "parent": f"{self.parent}/memoryBanks/{self.memory_bank_id}",
            "memory": {
                "user_id": user_id,
                "content": content,
                "scope": scope.upper(),
            },
        }
        self._client.create_memory(request=request)

    def recall_memories(self, user_id: str, query: str, top_k: int = 5) -> list[str]:
        """Retrieve memories relevant to a query for a given user.

        Args:
            user_id:  The user whose memories to search.
            query:    Semantic query string.
            top_k:    Maximum number of memories to return.

        Returns:
            List of memory content strings, most relevant first.
        """
        if not self._client or not self.memory_bank_id:
            print(f"[mock] recall_memories: user={user_id}, query={query[:60]}")
            return []

        # VERIFY: QueryMemoriesRequest proto structure
        request = {
            "name": f"{self.parent}/memoryBanks/{self.memory_bank_id}",
            "user_id": user_id,
            "query": query,
            "top_k": top_k,
        }
        response = self._client.query_memories(request=request)
        return [m.content for m in response.memories]


# ─── Session ID mapper ────────────────────────────────────────────────────────

class SessionMapper:
    """
    Maps external CRM ticket IDs to ADK session IDs.

    Agents use ADK's session_id for their own state. But your CRM uses ticket IDs.
    This mapper keeps them in sync so you can resume an agent session given
    only a ticket ID from your CRM.
    """

    def __init__(self) -> None:
        self._map: dict[str, str] = {}

    def register(self, ticket_id: str, session_id: str) -> None:
        self._map[ticket_id] = session_id

    def get_session_id(self, ticket_id: str) -> str | None:
        return self._map.get(ticket_id)

    def all_mappings(self) -> dict[str, str]:
        return dict(self._map)


# ─── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Agent Memory Bank — demo (mock mode if SDK not yet available)\n")

    memory = AgentMemoryBank()

    # Store a user preference
    memory.store_memory(
        user_id="u-alice",
        content="Prefers resolution steps via email, not through the support portal. Timezone: US/Pacific.",
        scope="user",
    )

    # Store a historical fact about a customer
    memory.store_memory(
        user_id="u-megacorp",
        content="Filed a billing dispute in February 2026 (T-0998). Dispute was resolved in their favour — $2,100 credit issued.",
        scope="user",
    )

    # Recall memories for the Megaticket scenario
    memories = memory.recall_memories(
        user_id="u-megacorp",
        query="billing dispute refund history",
    )
    print("Recalled memories for u-megacorp:", memories or "[mock — no real memories stored yet]")

    # Session mapper demo
    mapper = SessionMapper()
    mapper.register("T-megaticket-001", "adk-session-abc123")
    print("\nSession map:", mapper.all_mappings())
