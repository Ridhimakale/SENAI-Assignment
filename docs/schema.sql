-- SenAI CRM Intelligence Platform
-- Submission-ready logical SQL schema
-- Source of truth: backend/app/models/*.py and backend/alembic/versions/20260610_0001_initial_foundation_schema.py
--
-- Note:
-- The project uses a native vector-style embedding column for knowledge_chunks.embedding.
-- FAISS remains the runtime vector index, while the database column stores the persisted embedding payload.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

DO $$ BEGIN
    CREATE TYPE contact_status AS ENUM ('VIP', 'Blocked', 'Active', 'Churned');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE thread_status AS ENUM ('Open', 'Resolved', 'Escalated', 'Ignored');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE email_status AS ENUM ('Received', 'Processing', 'Replied', 'Escalated', 'Ignored');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE email_category AS ENUM (
        'Complaint',
        'Inquiry',
        'Bug Report',
        'Feature Request',
        'Compliance',
        'Legal',
        'Billing',
        'Spam',
        'Internal',
        'Other'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE email_urgency AS ENUM ('Critical', 'High', 'Medium', 'Low');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE action_type AS ENUM ('Auto-Reply', 'Escalate', 'Legal-Flag', 'Ticket-Created', 'Ignored');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE action_status AS ENUM ('Proposed', 'Executed', 'Blocked', 'Failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE job_status AS ENUM ('Queued', 'Processing', 'Completed', 'Failed', 'Skipped');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ticket_status AS ENUM ('Open', 'InProgress', 'Resolved');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE classification_validation_status AS ENUM ('Valid', 'Invalid', 'Repaired', 'Failed');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE web_intelligence_status AS ENUM ('Success', 'Failed', 'SkippedRobots');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    name VARCHAR(255),
    company VARCHAR(255),
    status contact_status NOT NULL DEFAULT 'Active',
    vip_reason VARCHAR(255),
    account_value NUMERIC(12, 2),
    churn_risk_score DOUBLE PRECISION NOT NULL DEFAULT 0,
    subscription_tier VARCHAR(100),
    renewal_status VARCHAR(100),
    open_ticket_count INTEGER NOT NULL DEFAULT 0,
    metadata_json JSONB,
    last_contact_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_contacts_status ON contacts (status);
CREATE INDEX IF NOT EXISTS ix_contacts_company ON contacts (company);
CREATE INDEX IF NOT EXISTS ix_contacts_churn_risk_score ON contacts (churn_risk_score);

CREATE TABLE IF NOT EXISTS processing_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) NOT NULL UNIQUE,
    status job_status NOT NULL DEFAULT 'Queued',
    stage VARCHAR(100) NOT NULL DEFAULT 'INGESTED',
    error_code VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_processing_jobs_status ON processing_jobs (status);
CREATE INDEX IF NOT EXISTS ix_processing_jobs_stage ON processing_jobs (stage);

CREATE TABLE IF NOT EXISTS threads (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    contact_id INTEGER NOT NULL REFERENCES contacts(id),
    subject VARCHAR(500),
    sender_email VARCHAR(320) NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL,
    last_updated_at TIMESTAMPTZ NOT NULL,
    status thread_status NOT NULL DEFAULT 'Open',
    assigned_to VARCHAR(255),
    priority_score INTEGER NOT NULL DEFAULT 0,
    message_count INTEGER NOT NULL DEFAULT 0,
    last_sentiment_score DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_threads_thread_sender UNIQUE (thread_id, sender_email)
);

CREATE INDEX IF NOT EXISTS ix_threads_sender_email ON threads (sender_email);
CREATE INDEX IF NOT EXISTS ix_threads_contact_id ON threads (contact_id);
CREATE INDEX IF NOT EXISTS ix_threads_status ON threads (status);
CREATE INDEX IF NOT EXISTS ix_threads_last_updated_at ON threads (last_updated_at);

CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    thread_id INTEGER NOT NULL REFERENCES threads(id),
    contact_id INTEGER NOT NULL REFERENCES contacts(id),
    processing_job_id INTEGER REFERENCES processing_jobs(id),
    message_id VARCHAR(255) NOT NULL UNIQUE,
    sender VARCHAR(320) NOT NULL,
    subject VARCHAR(500),
    normalized_subject VARCHAR(500),
    body TEXT NOT NULL,
    body_preview VARCHAR(500),
    body_truncated BOOLEAN NOT NULL DEFAULT FALSE,
    timestamp TIMESTAMPTZ NOT NULL,
    sentiment_score DOUBLE PRECISION,
    category email_category,
    urgency email_urgency,
    requires_human BOOLEAN NOT NULL DEFAULT FALSE,
    confidence DOUBLE PRECISION,
    raw_entities JSONB,
    status email_status NOT NULL DEFAULT 'Received',
    priority_score INTEGER NOT NULL DEFAULT 0,
    heuristic_flags JSONB,
    classification_raw JSONB,
    classification_error TEXT,
    rag_context JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_emails_thread_timestamp ON emails (thread_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_emails_sender_timestamp ON emails (sender, timestamp);
CREATE INDEX IF NOT EXISTS ix_emails_status ON emails (status);
CREATE INDEX IF NOT EXISTS ix_emails_category ON emails (category);
CREATE INDEX IF NOT EXISTS ix_emails_urgency ON emails (urgency);
CREATE INDEX IF NOT EXISTS ix_emails_requires_human ON emails (requires_human);
CREATE INDEX IF NOT EXISTS ix_emails_priority_score ON emails (priority_score);
CREATE INDEX IF NOT EXISTS ix_emails_sentiment_score ON emails (sentiment_score);

CREATE TABLE IF NOT EXISTS actions (
    id SERIAL PRIMARY KEY,
    email_id INTEGER NOT NULL REFERENCES emails(id),
    agent_reasoning_log JSONB,
    action_type action_type NOT NULL,
    proposed_content TEXT,
    is_approved BOOLEAN NOT NULL DEFAULT FALSE,
    approved_by VARCHAR(255),
    executed_at TIMESTAMPTZ,
    status action_status NOT NULL DEFAULT 'Proposed',
    safety_block_reason TEXT,
    tool_name VARCHAR(255),
    tool_input JSONB,
    tool_output JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_actions_email_id ON actions (email_id);
CREATE INDEX IF NOT EXISTS ix_actions_action_type ON actions (action_type);
CREATE INDEX IF NOT EXISTS ix_actions_status ON actions (status);
CREATE INDEX IF NOT EXISTS ix_actions_executed_at ON actions (executed_at);

CREATE TABLE IF NOT EXISTS classification_runs (
    id SERIAL PRIMARY KEY,
    email_id INTEGER NOT NULL REFERENCES emails(id),
    prompt_version VARCHAR(100) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    classification_output JSONB,
    confidence DOUBLE PRECISION,
    validation_status classification_validation_status NOT NULL,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_classification_runs_email_id ON classification_runs (email_id);
CREATE INDEX IF NOT EXISTS ix_classification_runs_prompt_version ON classification_runs (prompt_version);
CREATE INDEX IF NOT EXISTS ix_classification_runs_model_name ON classification_runs (model_name);

CREATE TABLE IF NOT EXISTS internal_tickets (
    id SERIAL PRIMARY KEY,
    email_id INTEGER NOT NULL REFERENCES emails(id),
    thread_id INTEGER NOT NULL REFERENCES threads(id),
    title VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    assignee VARCHAR(255),
    priority VARCHAR(50) NOT NULL,
    status ticket_status NOT NULL DEFAULT 'Open',
    created_by VARCHAR(255) NOT NULL DEFAULT 'agent',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_internal_tickets_email_id ON internal_tickets (email_id);
CREATE INDEX IF NOT EXISTS ix_internal_tickets_thread_id ON internal_tickets (thread_id);
CREATE INDEX IF NOT EXISTS ix_internal_tickets_status ON internal_tickets (status);
CREATE INDEX IF NOT EXISTS ix_internal_tickets_priority ON internal_tickets (priority);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    id SERIAL PRIMARY KEY,
    source_doc VARCHAR(255) NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    embedding_model VARCHAR(255) NOT NULL,
    embedding_hash VARCHAR(255),
    faiss_vector_id INTEGER,
    embedding VECTOR(384),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_knowledge_source_chunk UNIQUE (source_doc, chunk_index)
);

CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_source_doc ON knowledge_chunks (source_doc);
CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_faiss_vector_id ON knowledge_chunks (faiss_vector_id);

CREATE TABLE IF NOT EXISTS web_intelligence_cache (
    id SERIAL PRIMARY KEY,
    source_url VARCHAR(1000) NOT NULL,
    target_entity VARCHAR(255) NOT NULL,
    source_type VARCHAR(100) NOT NULL,
    scraped_data JSONB,
    scraped_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    status web_intelligence_status NOT NULL,
    error_message TEXT,
    robots_allowed BOOLEAN,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_web_intelligence_target_entity ON web_intelligence_cache (target_entity);
CREATE INDEX IF NOT EXISTS ix_web_intelligence_source_url ON web_intelligence_cache (source_url);
CREATE INDEX IF NOT EXISTS ix_web_intelligence_expires_at ON web_intelligence_cache (expires_at);
CREATE INDEX IF NOT EXISTS ix_web_intelligence_target_expires ON web_intelligence_cache (target_entity, expires_at);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL,
    entity_id INTEGER NOT NULL,
    action VARCHAR(100) NOT NULL,
    performed_by VARCHAR(255) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    diff JSONB,
    request_id VARCHAR(100),
    correlation_id VARCHAR(100),
    metadata_json JSONB
);

CREATE INDEX IF NOT EXISTS ix_audit_entity ON audit_log (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS ix_audit_timestamp ON audit_log (timestamp);
CREATE INDEX IF NOT EXISTS ix_audit_performed_by ON audit_log (performed_by);
