# Backup Plan

## PostgreSQL

Run a daily logical backup:

```powershell
pg_dump --format=custom --file=course_agent_$(Get-Date -Format yyyyMMdd).dump $env:DATABASE_URL
```

Keep at least 7 daily and 4 weekly snapshots.

## Object Storage

Mirror the MinIO bucket to another storage location:

```powershell
mc mirror minio/course-materials backup/course-materials
```

Keep object storage backups aligned with database backups because material metadata and object keys are linked.
