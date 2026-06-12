# Database Schema Explanation

This project uses a normalized relational schema to support email ingestion, thread grouping, AI classification, agent actions, RAG retrieval, web intelligence, and audit tracking.

## Core Design

- `contacts` stores customer profile and risk metadata.
- `threads` groups related emails by sender and thread identity.
- `emails` stores the raw message, AI classification output, heuristics, and RAG context.
- `actions` stores agent decisions, draft replies, tool calls, and reasoning logs.
- `classification_runs` stores versioned classification outputs for auditability.
- `internal_tickets` stores escalations created by the agent or human workflow.
- `processing_jobs` tracks ingestion and streaming simulation jobs.
- `knowledge_chunks` stores RAG chunks and their embedding vector.
- `web_intelligence_cache` stores cached public sentiment and scraping results.
- `audit_log` stores change history for traceability.

## Vector Column

The `knowledge_chunks.embedding` column stores a 384-dimensional embedding vector used by the RAG pipeline.
This supports semantic similarity search over internal knowledge base documents.

## JSON Fields

JSONB is used where the data is flexible or nested:

- `contacts.metadata_json`
- `emails.raw_entities`
- `emails.heuristic_flags`
- `emails.classification_raw`
- `emails.rag_context`
- `actions.agent_reasoning_log`
- `actions.tool_input`
- `actions.tool_output`
- `classification_runs.classification_output`
- `web_intelligence_cache.scraped_data`
- `audit_log.diff`
- `audit_log.metadata_json`

## Why This Design

- Normalized tables make the schema easy to query and maintain.
- JSONB fields allow flexible AI metadata without unnecessary table expansion.
- The vector column supports retrieval-augmented generation.
- Audit tracking preserves explainability and debugging history.

