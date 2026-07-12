# Database Migration Notes

1. Backup PostgreSQL before each release.
2. Run `alembic current` and confirm the current revision.
3. Run `alembic upgrade head`.
4. Verify `/api/v1/readyz`.
5. If rollback is required, restore the backup first, then deploy the previous app image.

The application expects pgvector support for `material_chunks.embedding`.
