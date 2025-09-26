# Remaining Setup Requirements for Full Functionality

## Current Status
✅ **Demo Running**: Clean, professional UI without emojis at http://localhost:8504
✅ **API Keys Configured**: OpenAI and Supabase credentials in place
✅ **Cost Optimization**: Using GPT-3.5-turbo with 500 token limit
✅ **UI Complete**: Shadcn-inspired professional design

## 🔴 CRITICAL: Required for Full Functionality

### 1. **Supabase Database Setup**
The system needs the vector database populated with NSW legislation documents.

#### Required Tables:
```sql
-- Create documents table
CREATE TABLE documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    act_name TEXT NOT NULL,
    section_number TEXT,
    content TEXT NOT NULL,
    keywords TEXT[],
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create embeddings table with vector column
CREATE TABLE document_embeddings (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    embedding vector(1536),  -- OpenAI embedding dimension
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create index for similarity search
CREATE INDEX ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create similarity search function
CREATE OR REPLACE FUNCTION similarity_search(
    query_embedding vector,
    similarity_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    content TEXT,
    act_name TEXT,
    section_number TEXT,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        de.id,
        de.document_id,
        d.content,
        d.act_name,
        d.section_number,
        1 - (de.embedding <=> query_embedding) as similarity
    FROM document_embeddings de
    JOIN documents d ON de.document_id = d.id
    WHERE 1 - (de.embedding <=> query_embedding) > similarity_threshold
    ORDER BY de.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

### 2. **Document Processing Pipeline (KAN-3)**
The document processing system needs to be run to populate the database.

#### Steps Required:
```bash
# 1. Install additional dependencies
pip install datasets supabase vecs openai

# 2. Run the document processor
python data/process_legislation.py

# This will:
# - Download NSW legislation from Hugging Face dataset
# - Filter for NSW Revenue acts
# - Generate embeddings using OpenAI
# - Store in Supabase vector database
```

#### Create Processing Script:
```python
# data/process_legislation.py
import os
from datasets import load_dataset
from openai import OpenAI
from supabase import create_client
import json

# Initialize clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# NSW Revenue Acts to process
NSW_REVENUE_ACTS = [
    "Duties Act 1997",
    "Payroll Tax Act 2007",
    "Land Tax Act 1956",
    "Land Tax Management Act 1956",
    "Revenue Administration Act 1996",
    "Fines Act 1996",
    "First Home Owner Grant (New Homes) Act 2000"
]

def process_documents():
    # Load dataset
    dataset = load_dataset("isaacus/open-australian-legal-corpus", split="train")

    # Filter for NSW Revenue legislation
    nsw_docs = []
    for doc in dataset:
        if any(act in doc.get('title', '') for act in NSW_REVENUE_ACTS):
            nsw_docs.append(doc)

    # Process each document
    for doc in nsw_docs:
        # Generate embedding
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=doc['content'][:8000]  # Limit content length
        )
        embedding = response.data[0].embedding

        # Store in Supabase
        supabase.table('documents').insert({
            'act_name': doc['title'],
            'content': doc['content'],
            'metadata': {'source': 'huggingface'}
        }).execute()

        # Store embedding
        supabase.table('document_embeddings').insert({
            'document_id': doc_id,
            'embedding': embedding
        }).execute()

if __name__ == "__main__":
    process_documents()
```

### 3. **Install Full Python Dependencies**
```bash
pip install -r requirements.txt
```

Missing packages that need installation:
- `supabase>=2.0.0`
- `vecs>=0.4.0`
- `openai>=1.0.0`
- `pandas>=2.0.0`
- `numpy>=1.24.0`
- `python-dotenv>=1.0.0`
- `structlog>=23.0.0`

### 4. **Environment Variable Validation**
Ensure all environment variables are properly set:

```bash
# Check if variables are loaded
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required = ['OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
for var in required:
    val = os.getenv(var)
    if val:
        print(f'✅ {var}: {val[:20]}...')
    else:
        print(f'❌ {var}: Missing!')
"
```

### 5. **Test Database Connection**
```python
# test_connection.py
import os
from supabase import create_client

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

supabase = create_client(url, key)

# Test query
try:
    result = supabase.table('documents').select('*').limit(1).execute()
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```

## 🟡 Optional Enhancements

### 1. **Production Deployment**
- Deploy to Railway or Streamlit Community Cloud
- Set up custom domain
- Configure SSL certificates
- Set up monitoring and logging

### 2. **Advanced Features**
- User authentication
- Query history persistence
- Export functionality
- Analytics dashboard

### 3. **Performance Optimization**
- Implement caching layer
- Add rate limiting
- Optimize embedding generation
- Batch processing for documents

## Quick Start Commands

```bash
# 1. Install dependencies
pip install supabase vecs openai python-dotenv streamlit

# 2. Load environment variables
export $(cat .env | xargs)

# 3. Test database connection
python3 -c "from supabase import create_client; import os; client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY')); print('Connected!')"

# 4. Run the demo
python3 -m streamlit run demo_app_clean.py --server.port=8504

# 5. Access the application
open http://localhost:8504
```

## Summary

The application has a **professional, clean UI** running at http://localhost:8504 with:
- ✅ No emojis in the interface
- ✅ Shadcn-inspired design system
- ✅ Cost-optimized API usage
- ✅ Professional demo mode

To make it **fully functional**, you need to:
1. **Set up Supabase tables** with pgvector extension
2. **Run document processing** to populate the database
3. **Install remaining dependencies** from requirements.txt
4. **Validate all connections** are working

The demo mode currently shows pre-configured responses. With the database populated, the system will:
- Search actual NSW legislation
- Generate real-time responses
- Validate through dual-agent system
- Provide accurate legal citations