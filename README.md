SENAI CRM Intelligence Platform

1. Project Overview
   1. This project is an AI-powered CRM operations platform that ingests customer emails, groups them into threads, applies deterministic heuristics first, grounds decisions in internal policy documents with RAG, classifies the request with an LLM, and then uses a single ReAct-style agent to decide whether to draft a reply, escalate, or create an internal workflow.
   2. The system is designed as a modular monolith rather than microservices. That choice keeps the project easier to understand, easier to test, and easier to defend in a submission setting.
   3. The main product goal is not just email classification. The goal is to understand the conversation, use the right tools, explain the reasoning, and surface useful business analytics.

2. What Is Included
   1. FastAPI backend with request validation, OpenAPI generation, and async service structure.
   2. PostgreSQL database with normalized tables for contacts, threads, emails, actions, knowledge chunks, web intelligence cache, audit log, classification runs, processing jobs, and internal tickets.
   3. Alembic migrations for schema versioning.
   4. RAG pipeline using markdown knowledge base files, chunking, sentence-transformer embeddings, and FAISS retrieval.
   5. LLM classification flow with strict structured output and confidence-based human review.
   6. Single ReAct-style agent for action selection and reasoning trace generation.
   7. Live web intelligence support for reputation-sensitive cases.
   8. Analytics dashboard for sentiment, categories, response heatmaps, at-risk accounts, and performance metrics.
   9. Frontend dashboard with inbox, thread workspace, replay simulator, analytics, and draft controls.

3. Repository Structure
   1. `backend/` contains the FastAPI app, models, schemas, repositories, services, API routes, and Alembic migrations.
   2. `frontend/` contains the Vite React application.
   3. `knowledge_base/` contains the markdown files used for RAG.
   4. `docs/` contains the ER diagram, SQL schema, schema explanation, migrations notes, and OpenAPI specification.
   5. `email-data-advanced.json` is the provided dataset used by the replay simulator.

4. Architecture Summary
   1. Email enters the system through ingestion.
   2. Validation, deduplication, thread linking, and priority scoring happen first.
   3. Heuristic rules handle spam, security, internal mail, and urgency before any LLM call.
   4. If the case is not immediately escalated, the system loads thread context and relevant policy snippets through RAG.
   5. The LLM returns a strict JSON classification result.
   6. The agent then decides whether to draft, escalate, flag for legal, create a ticket, or send a reply.
   7. Every important decision is persisted and later surfaced in analytics and the dashboard.

5. Key Design Decisions And Trade-Offs
   1. Modular monolith over microservices.
      1. This is a take-home assessment with limited scope and a small dataset.
      2. A modular monolith reduces deployment complexity and debugging overhead.
      3. It also keeps the architecture easy to explain during evaluation.
   2. FastAPI over a custom HTTP stack.
      1. FastAPI gives async support, strong validation, and automatic OpenAPI generation.
      2. That makes the backend easier to inspect and easier to test.
   3. PostgreSQL over a document-only store.
      1. The project needs normalized relationships for contacts, threads, emails, actions, and audit logs.
      2. PostgreSQL also gives JSON support for structured AI outputs and rich filtering for analytics.
   4. FAISS over a heavier vector database.
      1. The knowledge base is small and fixed for the assessment.
      2. FAISS is lightweight, fast, and avoids introducing unnecessary infrastructure.
   5. Sentence-transformers embeddings.
      1. The model `sentence-transformers/all-MiniLM-L6-v2` is fast and good enough for a compact policy corpus.
      2. It gives a practical balance between quality and simplicity.
   6. Single ReAct agent instead of multi-agent orchestration.
      1. The workflows are limited and the dataset is small.
      2. A single agent is easier to debug and easier to explain.
      3. It still supports tool use, reasoning traces, and action execution.
   7. Heuristics before LLM.
      1. Spam, security, and internal routing should not depend on model guesswork.
      2. This protects the system from unsafe automation.
   8. Confidence threshold for human review.
      1. If classification confidence is below `0.70`, the system flags the email for human review.
      2. That reduces the chance of overconfident mistakes in legal, compliance, and churn-sensitive cases.
   9. Web intelligence caching.
      1. Reputation checks are cached for six hours.
      2. This avoids repeated scraping and keeps the main pipeline non-blocking.

6. Environment Variables
   1. Create a `.env` file in the repository root for backend settings.
   2. Use the values from `.env.example` as the base template.
   3. Required backend variables:
      1. `APP_NAME` is the display name of the app.
      2. `APP_VERSION` is the version string.
      3. `ENVIRONMENT` controls the runtime environment.
      4. `LOG_LEVEL` controls logging verbosity.
      5. `DATABASE_URL` points to PostgreSQL.
      6. `KNOWLEDGE_BASE_PATH` points to the markdown knowledge base folder.
      7. `RAG_INDEX_PATH` points to the FAISS index storage directory.
      8. `EMBEDDING_MODEL_NAME` sets the embedding model.
      9. `RAG_TOP_K` controls retrieval depth.
      10. `OPENAI_API_KEY` is used if you want OpenAI-backed inference.
      11. `OPENAI_MODEL` sets the OpenAI model name.
      12. `CLASSIFIER_PROMPT_VERSION` tracks the prompt version used for classification.
      13. `CLASSIFIER_CONFIDENCE_THRESHOLD` sets the human-review cutoff.
      14. `GROQ_API_KEY` is used for Groq-backed generation.
      15. `GROQ_MODEL` sets the Groq model name.
      16. `AGENT_MAX_TOOL_CALLS` limits the number of agent tool calls per email.
   4. Optional frontend variable:
      1. `VITE_API_BASE_URL` can be placed in `frontend/.env` or `frontend/.env.local`.
      2. If omitted, the frontend defaults to `http://127.0.0.1:8000`.

7. Setup Guide
   1. Install PostgreSQL and create a database named `senai_crm`.
   2. Create the root `.env` file and fill in the backend values.
   3. Install backend dependencies.
      1. `python -m pip install -r backend/requirements.txt`
   4. Apply database migrations.
      1. `alembic -c backend/alembic.ini upgrade head`
   5. Start the backend API.
      1. `python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`
   6. Install frontend dependencies.
      1. `npm install`
      2. Run this inside the `frontend/` folder.
   7. Start the frontend.
      1. `npm run dev`
      2. This uses Vite on `http://127.0.0.1:5173` by default.
   8. If your frontend is running on a different local port, update backend CORS and `VITE_API_BASE_URL` to match.

8. How To Seed The Knowledge Base
   1. Place the markdown policy files in the `knowledge_base/` folder.
   2. The required files are:
      1. `pricing_policy.md`
      2. `sla_policy.md`
      3. `refund_policy.md`
      4. `api_docs.md`
      5. `compliance_faq.md`
      6. `escalation_matrix.md`
   3. The RAG service automatically reads all markdown files in that folder, chunks them, embeds them, and builds the FAISS index on first use.
   4. The index is currently kept in memory for simplicity, so after editing the knowledge base you should restart the backend or trigger a fresh RAG search to rebuild it.
   5. You can verify the knowledge base through `GET /rag/search?q=...`.

9. How To Run The Email Simulation
   1. Make sure the backend is running on port `8000`.
   2. Open the frontend and go to `Replay Simulator`.
   3. Use the dataset path `email-data-advanced.json`.
   4. Keep `Dry Run` unchecked if you want real ingestion into the backend.
   5. Click `Run Simulation`.
   6. The simulator will replay emails through `POST /api/simulate/stream`, which then feeds each email into the ingestion pipeline.
   7. If you only want a preview without writing to the database, enable `Dry Run`.
   8. If the backend is unavailable, the UI can fall back to demo mode, but that is only for local preview.

10. Backend Workflow
   1. Ingestion validates the email payload.
   2. Duplicate `message_id` values are rejected through idempotency checks.
   3. Threads are linked or created.
   4. Priority is assigned using heuristic scoring.
   5. Spam, internal, urgency, and security rules run immediately.
   6. Thread history and RAG context are collected.
   7. The classification engine produces structured output with category, sentiment, urgency, confidence, and entities.
   8. The agent decides whether to draft, escalate, or create a ticket.
   9. Actions and audit logs are stored.
   10. Analytics queries later read the stored data for the dashboard.

11. RAG Behavior
   1. Chunk size is designed around the 300 to 500 token range with overlap.
   2. Chunks are embedded and stored in FAISS.
   3. Retrieval returns the top relevant chunks with source attribution.
   4. The response draft can insert policy snippets so the reply is grounded in internal documentation.
   5. The system is designed so retrieval is separate from generation, which keeps the pipeline auditable.

12. Classification And Agent Behavior
   1. Classification output is structured JSON.
   2. The output includes category, sentiment, sentiment score, urgency, requires_human, escalation_reason, suggested_reply, confidence, and detected_entities.
   3. Low confidence cases are routed to human review.
   4. The agent owns action selection.
   5. The agent can use tools for thread history, contact profile, account status, legal flagging, ticket creation, and draft generation.
   6. The agent keeps a reasoning trace so each decision can be explained later.

13. Analytics And Dashboard
   1. Sentiment trend shows how sentiment changes over time.
   2. Category breakdown shows what kinds of emails dominate the queue.
   3. Response heatmap shows when support activity is concentrated during the day.
   4. At-risk accounts shows customers with negative streaks or unresolved threads.
   5. Agent performance shows auto-reply rate, escalation rate, total actions, and average confidence.
   6. The dashboard is intentionally connected to both live data and graceful fallback data so it stays usable in demo scenarios.

14. Known Limitations
   1. The FAISS index is in-memory in this version, so it is rebuilt on process restart.
   2. Live web intelligence is cached and intentionally conservative, so it may fall back when data is unavailable.
   3. External outbound email sending is not enabled as a live production integration in this submission.
   4. Some dashboard views can fall back to seeded demo values if live analytics are sparse, which keeps the demo readable.
   5. The agent is intentionally single-agent rather than multi-agent for clarity and maintainability.
   6. The project is optimized for the assessment dataset and submission demo, not for large-scale production load.

15. Validation And Useful Endpoints
   1. Health check:
      1. `GET /health`
   2. Email ingestion:
      1. `POST /api/ingest`
   3. Replay simulation:
      1. `POST /api/simulate/stream`
   4. RAG search:
      1. `GET /rag/search?q=...`
   5. Analytics:
      1. `GET /analytics/sentiment-trend?days=30`
      2. `GET /analytics/category-breakdown`
      3. `GET /analytics/response-heatmap`
      4. `GET /analytics/at-risk-accounts`
      5. `GET /analytics/agent-performance`
   6. Thread and contact views:
      1. `GET /threads/{contact_email}`
      2. `GET /contacts/{email}`

16. Submission Notes
   1. The repository includes the database schema, ER diagram, OpenAPI spec, and migrations documentation under `docs/`.
   2. The UI supports the inbox, thread workspace, analytics dashboard, and replay simulator.
   3. The system is intentionally explainable, traceable, and safe for risky customer cases.
  

