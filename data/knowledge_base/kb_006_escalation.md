---
id: kb-006
title: When to escalate to a human agent
category: meta
---

This article is for the Operations Council itself, not for end users. It defines the criteria the Steward agent uses to decide whether a ticket needs human review.

## Escalate to a human when:

- The ticket involves a refund or credit decision over $500
- The ticket mentions legal action, regulatory action, or formal complaint language
- The ticket includes a security incident report (compromised account, data exposure, etc.)
- The ticket mentions self-harm, harassment, or other safety-sensitive content
- The Loremaster cannot find a relevant knowledge base article AND the Triage Scout's confidence score is below 0.6
- The ticket has been escalated by the user with phrases like "this is urgent," "I need a human," or "please escalate"

## Do not escalate when:

- The ticket has a clear, documented answer in the knowledge base
- The Triage Scout has classified the ticket with confidence above 0.85 AND the Loremaster has retrieved at least one article above the relevance threshold
- The user is asking for status on an existing ticket (route to status lookup, not escalation)

## How to escalate

The Steward issues a structured escalation by calling the `escalate_to_human` tool with:

- Original ticket text
- Triage classification and confidence
- Knowledge articles consulted (or "none found")
- Reason for escalation (one of the criteria above)

The escalation tool returns a human ticket ID that the Envoy includes in its response to the user.
