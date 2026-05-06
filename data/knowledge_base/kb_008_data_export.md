---
id: kb-008
title: Exporting your data from ContosoCloud
category: data
---

You can export your data from ContosoCloud at any time. Different services have different export options.

## Compute and storage

- **Cloud Storage buckets**: use `gsutil rsync` or the Storage Transfer Service to copy objects to another cloud or on-premises destination
- **Compute Engine disks**: snapshot the disk, then export the snapshot to Cloud Storage as a tar.gz

## Databases

- **Cloud SQL**: export to Cloud Storage as SQL dump or CSV, then download
- **Firestore**: use the managed export feature (writes to a Cloud Storage bucket you control)
- **BigQuery**: export query results or full tables to Cloud Storage as CSV, JSON, Parquet, or Avro

## Identity and admin data

For audit logs, IAM policies, and admin metadata, use the corresponding admin API. Each service publishes a `<service>.googleapis.com/export` endpoint that returns the structured data.

For full-account data export (across all services), open a request through the admin console under Privacy → Data export. The export takes 24-72 hours depending on the volume.
