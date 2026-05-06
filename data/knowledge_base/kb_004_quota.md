---
id: kb-004
title: Quota and rate limit errors
category: limits
---

ContosoCloud applies quotas and rate limits to protect platform stability and prevent runaway costs. If you see an error like `RESOURCE_EXHAUSTED` or `QUOTA_EXCEEDED`:

1. Check your current quota usage at console.contosocloud.com → IAM & Admin → Quotas
2. Identify which quota is being hit (regional, project-level, or service-specific)
3. Submit a quota increase request through the same page

Standard quota increase requests are reviewed within 2 business days. Urgent requests for production workloads can be expedited by including "production-impacting" in the request notes.

Most rate limits reset every 60 seconds. If you're hitting transient rate limits, implement exponential backoff in your client.
