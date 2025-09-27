-- Manual fix for Supabase visibility issues
-- Run this in Supabase Dashboard → SQL Editor

-- 1. First check if our data actually exists
SELECT 'Checking if data exists...' as status;
SELECT COUNT(*) as total_records FROM nsw_documents;

-- 2. If data exists, show sample
SELECT 'Sample data:' as status;
SELECT id, act_name, revenue_type, section_title
FROM nsw_documents
LIMIT 3;

-- 3. Check table permissions
SELECT 'Checking permissions...' as status;
SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_name = 'nsw_documents';

-- 4. Fix permissions for dashboard access
SELECT 'Fixing permissions...' as status;
GRANT ALL ON TABLE nsw_documents TO anon, authenticated, service_role, postgres;
GRANT USAGE, SELECT ON SEQUENCE nsw_documents_id_seq TO anon, authenticated, service_role, postgres;

-- 5. Disable RLS to make table visible in dashboard
SELECT 'Disabling RLS...' as status;
ALTER TABLE nsw_documents DISABLE ROW LEVEL SECURITY;

-- 6. Create the execute_sql function that was missing
SELECT 'Creating execute_sql function...' as status;
CREATE OR REPLACE FUNCTION execute_sql(query text)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result json;
BEGIN
    EXECUTE query;
    GET DIAGNOSTICS result = ROW_COUNT;
    RETURN json_build_object('status', 'success', 'rows_affected', result);
END;
$$;

-- Grant permissions on the function
GRANT EXECUTE ON FUNCTION execute_sql(text) TO anon, authenticated, service_role;

-- 7. Create hybrid search function
SELECT 'Creating hybrid search function...' as status;
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

-- Grant permissions on hybrid search
GRANT EXECUTE ON FUNCTION hybrid_search(TEXT, vector, TEXT, INT) TO anon, authenticated, service_role;

-- 8. Force schema reload
SELECT 'Forcing schema reload...' as status;
NOTIFY pgrst, 'reload schema';

-- 9. Final verification
SELECT 'Final verification...' as status;
SELECT
    COUNT(*) as total_records,
    COUNT(DISTINCT revenue_type) as revenue_types,
    COUNT(DISTINCT act_name) as acts
FROM nsw_documents;

SELECT 'Setup complete!' as status;