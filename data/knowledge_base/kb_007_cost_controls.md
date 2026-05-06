---
id: kb-007
title: Setting cost controls and budget alerts
category: billing
---

Unexpectedly high cloud costs are usually preventable. ContosoCloud offers several layers of cost controls.

## Budget alerts

Configure budget alerts at console.contosocloud.com → Billing → Budgets:

- Set a monthly target spend
- Configure alerts at 50%, 90%, and 100% of the target
- Optionally configure a hard cap that pauses non-critical workloads when reached

## Quota-based cost controls

For any service, you can set a project-level quota that's lower than the default. Once the quota is hit, the service stops accepting new requests for the period. This is the most reliable way to put a hard ceiling on a specific cost driver.

## Per-service cost controls

- **AI Platform**: set a Spend Cap on Agent Platform that pauses agent traffic when reached
- **Cloud Run**: set max instances and per-request CPU/memory limits
- **BigQuery**: set per-query and per-day byte-processing limits

For high-cost services, use the cost optimization recommendations in the Billing section. They're refreshed daily and identify specific resources that are running at low utilization.
