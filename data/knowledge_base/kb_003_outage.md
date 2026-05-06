---
id: kb-003
title: Reporting an outage or degraded service
category: incident
---

If you're experiencing what you believe is a ContosoCloud outage or degraded service:

## First, check the status page

Visit https://status.contosocloud.com to see if there's an active incident. The status page shows:

- Active incidents with their detected start time and affected regions
- Recent resolved incidents from the last 7 days
- Per-service health (Compute, Storage, Database, Networking, AI Platform)

If your issue matches an active incident, you don't need to file a separate report. Subscribe to incident updates on the status page to receive notifications as the incident progresses.

## If your issue isn't on the status page

If you believe you're experiencing an outage that isn't reflected on the status page:

1. From the admin console, go to Support → Incidents → Report new
2. Provide: affected service, region, time the issue started, observed behavior, and expected behavior
3. Include a recent request ID or trace ID if you have one
4. Submit

Production incidents (Severity 1) are routed to the on-call engineering team within 5 minutes. Standard incidents are reviewed within 30 minutes during business hours.

## What does NOT qualify as an outage

- Quota or rate limit errors (these are working as intended; see kb-004)
- Permission denied errors (configuration; see kb-005)
- Performance variance within the published SLO range
