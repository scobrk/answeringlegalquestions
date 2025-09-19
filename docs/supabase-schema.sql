-- Revenue NSW AI Assistant Database Schema
-- To be applied to Supabase project

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Documents table for NSW legislation
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    act_name TEXT NOT NULL,
    section_number TEXT,
    subsection TEXT,
    effective_date DATE,
    last_amended DATE,
    document_type TEXT DEFAULT 'legislation',
    keywords TEXT[],
    embedding VECTOR(1536), -- OpenAI text-embedding-3-small dimension
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for efficient searching
CREATE INDEX documents_embedding_idx ON documents USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX documents_act_name_idx ON documents (act_name);
CREATE INDEX documents_section_idx ON documents (section_number);
CREATE INDEX documents_keywords_idx ON documents USING GIN (keywords);
CREATE INDEX documents_metadata_idx ON documents USING GIN (metadata);

-- Query logs for audit trail (KAN-8)
CREATE TABLE query_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id UUID NOT NULL DEFAULT gen_random_uuid(),

    -- Query details
    query_text TEXT NOT NULL,
    query_type TEXT,
    query_classification TEXT,

    -- Primary response details
    primary_answer TEXT,
    primary_confidence FLOAT,
    primary_citations JSONB,
    primary_generation_time FLOAT,

    -- Validation details
    validation_status TEXT, -- 'APPROVED', 'PARTIAL', 'REJECTED'
    validation_checks JSONB,
    validation_issues JSONB,
    validation_confidence FLOAT,
    validation_time FLOAT,

    -- Final response
    final_answer TEXT,
    total_processing_time FLOAT,

    -- Cost tracking
    embedding_tokens INTEGER,
    llm_tokens INTEGER,
    total_cost DECIMAL(10,4),

    -- Source documents used
    source_documents JSONB,
    model_versions JSONB,
    error_details JSONB
);

-- Create indexes for query logs
CREATE INDEX query_logs_timestamp_idx ON query_logs (timestamp DESC);
CREATE INDEX query_logs_session_idx ON query_logs (session_id);
CREATE INDEX query_logs_status_idx ON query_logs (validation_status);
CREATE INDEX query_logs_query_type_idx ON query_logs (query_type);

-- Document chunks for RAG retrieval
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_embedding VECTOR(1536),
    token_count INTEGER,
    overlap_start INTEGER DEFAULT 0,
    overlap_end INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for chunk retrieval
CREATE INDEX document_chunks_embedding_idx ON document_chunks USING ivfflat (chunk_embedding vector_cosine_ops);
CREATE INDEX document_chunks_document_idx ON document_chunks (document_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update timestamps
CREATE TRIGGER update_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- View for quick document search with relevance scoring
CREATE VIEW document_search AS
SELECT
    d.id,
    d.title,
    d.act_name,
    d.section_number,
    d.content,
    d.keywords,
    d.metadata,
    d.created_at
FROM documents d;

-- Sample data insert function (for testing)
CREATE OR REPLACE FUNCTION insert_sample_document(
    p_title TEXT,
    p_content TEXT,
    p_act_name TEXT,
    p_section TEXT DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    doc_id UUID;
BEGIN
    INSERT INTO documents (title, content, act_name, section_number)
    VALUES (p_title, p_content, p_act_name, p_section)
    RETURNING id INTO doc_id;

    RETURN doc_id;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed for security)
-- GRANT SELECT, INSERT, UPDATE ON documents TO authenticated;
-- GRANT SELECT, INSERT ON query_logs TO authenticated;
-- GRANT SELECT, INSERT, UPDATE ON document_chunks TO authenticated;