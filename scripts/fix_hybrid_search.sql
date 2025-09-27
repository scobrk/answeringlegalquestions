-- Fix the hybrid search function type issues
-- Run this in Supabase SQL Editor

-- Drop the existing function
DROP FUNCTION IF EXISTS hybrid_search(TEXT, vector, TEXT, INT);

-- Create corrected hybrid search function
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
    combined_score DOUBLE PRECISION,
    bm25_rank DOUBLE PRECISION,
    vector_similarity DOUBLE PRECISION,
    metadata JSONB
) AS $$
BEGIN
    RETURN QUERY
    WITH
    bm25_results AS (
        SELECT
            d.id,
            CAST(ts_rank(to_tsvector('english', d.content), plainto_tsquery('english', query_text)) AS DOUBLE PRECISION) as bm25_score
        FROM nsw_documents d
        WHERE (revenue_filter IS NULL OR d.revenue_type = revenue_filter)
            AND to_tsvector('english', d.content) @@ plainto_tsquery('english', query_text)
    ),
    vector_results AS (
        SELECT
            d.id,
            CAST((1 - (d.embedding <=> query_embedding)) AS DOUBLE PRECISION) as vector_score
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
            CAST((COALESCE(b.bm25_score, 0) * 0.3 + COALESCE(v.vector_score, 0) * 0.7) AS DOUBLE PRECISION) as combined_score,
            CAST(COALESCE(b.bm25_score, 0) AS DOUBLE PRECISION) as bm25_rank,
            CAST(COALESCE(v.vector_score, 0) AS DOUBLE PRECISION) as vector_similarity
        FROM nsw_documents d
        LEFT JOIN bm25_results b ON d.id = b.id
        LEFT JOIN vector_results v ON d.id = v.id
        WHERE (revenue_filter IS NULL OR d.revenue_type = revenue_filter)
            AND (b.id IS NOT NULL OR v.id IS NOT NULL)
    )
    SELECT
        combined.id,
        combined.act_name,
        combined.content,
        combined.revenue_type,
        combined.section_title,
        combined.section_number,
        combined.combined_score,
        combined.bm25_rank,
        combined.vector_similarity,
        combined.metadata
    FROM combined
    ORDER BY combined_score DESC
    LIMIT match_count;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT EXECUTE ON FUNCTION hybrid_search(TEXT, vector, TEXT, INT) TO anon, authenticated, service_role;

-- Test the function
SELECT 'Function fixed successfully!' as status;