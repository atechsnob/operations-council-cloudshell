"""
chapter_06_governance/agent_identity.py

Demonstrates Agent Identity provisioning — giving each Council member a
cryptographic identity so downstream systems can verify which agent produced
a response.

Agent Identity (announced at Next '26) assigns each deployed agent a
Google-managed service identity with a cryptographic attestation token.
This is the foundation for audit trails, compliance reports, and
zero-trust networking between agents.

VERIFY: AgentIdentityServiceClient and the proto method signatures below
reflect the announced API. Confirm import paths and request shapes against
the Agent Platform SDK release notes before deploying.
"""

import os
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ["PROJECT_ID"]
REGION = os.environ.get("REGION", "us-central1")


# ─── Agent Identity wrapper ───────────────────────────────────────────────────

class AgentIdentityManager:
    """
    Manages cryptographic identities for Operations Council agents.

    Each agent gets a unique identity that:
      - Proves which agent (not just which service account) made a call
      - Can be verified by Agent Gateway and downstream services
      - Appears in Cloud Audit Logs with agent-level granularity
    """

    AGENT_NAMES = ["Steward", "TriageScout", "Loremaster", "Envoy"]

    def __init__(self):
        # VERIFY: Correct import path post-SDK release
        try:
            from google.cloud.aiplatform_v1beta1 import AgentIdentityServiceClient  # type: ignore
            self._client = AgentIdentityServiceClient()
        except ImportError:
            print(
                "⚠️  AgentIdentityServiceClient not yet in this SDK version.\n"
                "   Running in mock mode — identity values are illustrative."
            )
            self._client = None

        self.parent = f"projects/{PROJECT_ID}/locations/{REGION}"
        self._identities: dict[str, str] = {}

    def provision_identity(self, agent_name: str) -> str:
        """Provision a cryptographic identity for a named agent.

        Args:
            agent_name: Human-readable name, e.g. "Steward"

        Returns:
            The fully-qualified identity resource name.
        """
        if not self._client:
            mock_id = f"{self.parent}/agentIdentities/{agent_name.lower()}-mock-id"
            self._identities[agent_name] = mock_id
            print(f"[mock] Provisioned identity for {agent_name}: {mock_id}")
            return mock_id

        # VERIFY: CreateAgentIdentityRequest proto structure
        request = {
            "parent": self.parent,
            "agent_identity": {
                "display_name": f"operations-council-{agent_name.lower()}",
                "description": f"Cryptographic identity for the Operations Council {agent_name} agent",
            },
        }
        response = self._client.create_agent_identity(request=request)
        identity_id = response.name
        self._identities[agent_name] = identity_id
        print(f"✅ Provisioned identity for {agent_name}: {identity_id}")
        return identity_id

    def provision_all(self) -> dict[str, str]:
        """Provision identities for all four Council agents."""
        return {name: self.provision_identity(name) for name in self.AGENT_NAMES}

    def get_attestation_token(self, agent_name: str) -> str:
        """Fetch a short-lived attestation token for the given agent.

        This token is attached to outbound calls so that Agent Gateway and
        downstream services can verify the caller.

        VERIFY: GetAttestationTokenRequest proto structure and token lifetime.
        """
        identity_id = self._identities.get(agent_name)
        if not identity_id or not self._client:
            return f"mock-attestation-token-{agent_name.lower()}"

        # VERIFY: Method name and request structure
        request = {"name": identity_id}
        response = self._client.get_attestation_token(request=request)
        return response.token

    def list_identities(self) -> list[dict]:
        """List all provisioned agent identities in this project."""
        if not self._client:
            return [
                {"agent": name, "identity": id_}
                for name, id_ in self._identities.items()
            ]

        request = {"parent": self.parent}
        response = self._client.list_agent_identities(request=request)
        return [{"name": identity.name, "display_name": identity.display_name} for identity in response]


# ─── Demo ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Agent Identity — provisioning Operations Council identities\n")
    print("Note: running in mock mode if SDK not yet available\n")

    manager = AgentIdentityManager()
    identities = manager.provision_all()

    print("\nProvisioned identities:")
    for agent, identity_id in identities.items():
        print(f"  {agent:15} → {identity_id}")

    print("\nSteward attestation token (short-lived, used by Agent Gateway):")
    token = manager.get_attestation_token("Steward")
    print(f"  {token[:80]}…" if len(token) > 80 else f"  {token}")

    print("\nWhy this matters:")
    print("  Without Agent Identity, your audit logs show which service account called Gemini.")
    print("  With Agent Identity, they show which AGENT called Gemini — Steward vs Loremaster.")
    print("  That distinction is what makes compliance audits tractable.")
