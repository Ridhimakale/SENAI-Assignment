# Migration Files

The database schema is versioned using Alembic migrations.

## Main Migration

- `backend/alembic/versions/20260610_0001_initial_foundation_schema.py`

## What the Migration Contains

- Table creation for all core CRM and AI tables
- Enum type creation for status and category fields
- Foreign keys and unique constraints
- Indexes for performance-sensitive queries
- JSONB columns for structured AI metadata
- Native vector-style support for `knowledge_chunks.embedding`

## Why Migrations Matter

- They document how the database evolved over time.
- They let the schema be recreated consistently in new environments.
- They provide a reliable source of truth for deployment and review.

## Related Files

- `docs/er_diagram.mmd`
- `docs/schema.sql`
- `backend/app/models/vector_type.py`

