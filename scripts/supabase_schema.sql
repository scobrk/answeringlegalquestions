-- NSW Revenue AI Assistant - Supabase Database Schema
-- Run this in the Supabase SQL Editor

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create documents table
CREATE TABLE IF NOT EXISTS nsw_documents (
    id SERIAL PRIMARY KEY,
    act_name TEXT NOT NULL,
    content TEXT NOT NULL,
    revenue_type TEXT NOT NULL,
    section_title TEXT,
    section_number TEXT,
    category TEXT,
    file_path TEXT,
    embedding vector(768), -- Legal-BERT dimensions
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for optimal performance
CREATE INDEX IF NOT EXISTS idx_nsw_documents_embedding ON nsw_documents USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_nsw_documents_fts ON nsw_documents USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_nsw_documents_revenue_type ON nsw_documents (revenue_type);
CREATE INDEX IF NOT EXISTS idx_nsw_documents_act_name ON nsw_documents (act_name);

-- Create hybrid search function (BM25 + vector similarity)
CREATE OR REPLACE FUNCTION hybrid_search(
    query_text TEXT,
    query_embedding vector(768),
    revenue_filter TEXT DEFAULT NULL,
    match_count INT DEFAULT 5
) RETURNS TABLE (
    id INT,
    act_name TEXT,
    content TEXT,
    revenue_type TEXT,
    section_title TEXT,
    section_number TEXT,
    combined_score FLOAT,
    bm25_rank FLOAT,
    vector_similarity FLOAT,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH
    bm25_results AS (
        SELECT
            d.id,
            ts_rank(to_tsvector('english', d.content), plainto_tsquery('english', query_text)) as bm25_score
        FROM nsw_documents d
        WHERE (revenue_filter IS NULL OR d.revenue_type = revenue_filter)
            AND to_tsvector('english', d.content) @@ plainto_tsquery('english', query_text)
    ),
    vector_results AS (
        SELECT
            d.id,
            1 - (d.embedding <=> query_embedding) as vector_score
        FROM nsw_documents d
        WHERE (revenue_filter IS NULL OR d.revenue_type = revenue_filter)
            AND d.embedding IS NOT NULL
    ),
    combined AS (
        SELECT
            d.id,
            d.act_name,
            d.content,
            d.revenue_type,
            d.section_title,
            d.section_number,
            d.metadata,
            -- Reciprocal Rank Fusion scoring (30% BM25, 70% vector)
            COALESCE(b.bm25_score, 0) * 0.3 + COALESCE(v.vector_score, 0) * 0.7 as combined_score,
            COALESCE(b.bm25_score, 0) as bm25_rank,
            COALESCE(v.vector_score, 0) as vector_similarity
        FROM nsw_documents d
        LEFT JOIN bm25_results b ON d.id = b.id
        LEFT JOIN vector_results v ON d.id = v.id
        WHERE (revenue_filter IS NULL OR d.revenue_type = revenue_filter)
            AND (b.id IS NOT NULL OR v.id IS NOT NULL)
    )
    SELECT * FROM combined
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to get available revenue types
CREATE OR REPLACE FUNCTION get_revenue_types()
RETURNS TABLE (revenue_type TEXT, document_count BIGINT) AS $$
BEGIN
    RETURN QUERY
    SELECT d.revenue_type, COUNT(*) as document_count
    FROM nsw_documents d
    GROUP BY d.revenue_type
    ORDER BY document_count DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;