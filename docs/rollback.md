# Rollback Plan

1. Stop new deployments and pause worker replicas.
2. Restore the previous backend and frontend build.
3. Restore PostgreSQL from the pre-release backup if migrations are not backward compatible.
4. Restore object storage only if material files changed during the failed release.
5. Run `/api/v1/healthz` and `/api/v1/readyz`.
6. Resume workers after API and database consistency are verified.
