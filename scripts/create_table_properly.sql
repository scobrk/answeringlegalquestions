-- Create the NSW documents table properly in Supabase
-- Run this in Supabase Dashboard → SQL Editor

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the table
CREATE TABLE nsw_documents (
    id SERIAL PRIMARY KEY,
    act_name TEXT NOT NULL,
    content TEXT NOT NULL,
    revenue_type TEXT NOT NULL,
    section_title TEXT,
    section_number TEXT,
    category TEXT,
    file_path TEXT,
    embedding vector(768),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Create indexes
CREATE INDEX idx_nsw_documents_revenue_type ON nsw_documents (revenue_type);
CREATE INDEX idx_nsw_documents_act_name ON nsw_documents (act_name);
CREATE INDEX idx_nsw_documents_fts ON nsw_documents USING gin(to_tsvector('english', content));

-- 4. Set permissions
GRANT ALL ON TABLE nsw_documents TO anon, authenticated, service_role, postgres;
GRANT USAGE, SELECT ON SEQUENCE nsw_documents_id_seq TO anon, authenticated, service_role, postgres;

-- 5. Disable RLS for now
ALTER TABLE nsw_documents DISABLE ROW LEVEL SECURITY;

-- 6. Create hybrid search function
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
            -- Weighted scoring (30% BM25, 70% vector)
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

-- 7. Grant permissions on function
GRANT EXECUTE ON FUNCTION hybrid_search(TEXT, vector, TEXT, INT) TO anon, authenticated, service_role;

-- 8. Verify table was created
SELECT 'Table created successfully!' as status;
SELECT COUNT(*) as record_count FROM nsw_documents;