-- PostgreSQL schema (pgvector optional extension for embeddings)

CREATE TABLE conversations (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(128) NOT NULL,
    tenant_id VARCHAR(64) NOT NULL DEFAULT 'default',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_tenant_id ON conversations(tenant_id);

CREATE TABLE messages (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(id),
    role VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);

CREATE TABLE tool_calls (
    id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(id),
    tool_name VARCHAR(128) NOT NULL,
    idempotency_key VARCHAR(128) NOT NULL UNIQUE,
    input_summary TEXT NOT NULL,
    output_summary TEXT NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    latency_ms DOUBLE PRECISION,
    actor VARCHAR(128) NOT NULL,
    approval_id VARCHAR(128),
    correlation_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_tool_calls_conversation_id ON tool_calls(conversation_id);
CREATE INDEX idx_tool_calls_tool_name ON tool_calls(tool_name);

CREATE TABLE audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    actor VARCHAR(128) NOT NULL,
    action VARCHAR(128) NOT NULL,
    risk_level VARCHAR(16) NOT NULL DEFAULT 'low',
    details_json TEXT NOT NULL,
    correlation_id VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);

-- Optional pgvector table for document chunks
-- CREATE EXTENSION IF NOT EXISTS vector;
-- CREATE TABLE document_chunks (
--     id VARCHAR(64) PRIMARY KEY,
--     document_id VARCHAR(64) NOT NULL,
--     content TEXT NOT NULL,
--     metadata JSONB NOT NULL DEFAULT '{}',
--     embedding vector(1536)
-- );
-- CREATE INDEX idx_document_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
