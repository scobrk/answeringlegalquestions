# Supabase Setup Guide

## Step 1: Create Supabase Project

1. Go to [supabase.com](https://supabase.com) and create an account
2. Create a new project
3. Choose a region (preferably close to your location)
4. Set a database password (save this securely)
5. Wait for project provisioning (usually 2-3 minutes)

## Step 2: Enable pgvector Extension

1. Go to your project dashboard
2. Navigate to SQL Editor
3. Run the following command:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Step 3: Apply Database Schema

1. In the SQL Editor, copy and paste the contents of `docs/supabase-schema.sql`
2. Execute the script to create all tables and indexes
3. Verify tables were created successfully

## Step 4: Get Project Credentials

1. Go to Settings → API
2. Copy the following values:
   - **Project URL**: `https://your-project-ref.supabase.co`
   - **Anon/Public Key**: Your anonymous key for client connections
   - **Service Role Key**: Your service role key (keep secure)

## Step 5: Create Access Token

1. Go to Settings → Access Tokens
2. Create a new token named "Revenue NSW MCP Server"
3. Copy the token (you won't see it again)

## Step 6: Update Project Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Update `.env` with your Supabase credentials:
```env
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_ACCESS_TOKEN=your-access-token
```

3. Update `.mcp.json` with your project reference:
```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@supabase/mcp-server-supabase",
        "--read-only",
        "--project-ref=your-project-ref"
      ],
      "env": {
        "SUPABASE_ACCESS_TOKEN": "your-access-token"
      }
    }
  }
}
```

## Step 7: Test Connection

1. Restart Claude Code after updating `.mcp.json`
2. Try querying your Supabase project through the MCP
3. Verify you can see the created tables

## Database Schema Overview

### Core Tables

- **documents**: Stores NSW legislation with embeddings
- **document_chunks**: Chunked documents for RAG retrieval
- **query_logs**: Audit trail for all queries and responses

### Key Features

- **pgvector**: Vector similarity search for document retrieval
- **Indexes**: Optimized for fast searching and filtering
- **Audit Trail**: Complete logging for compliance and debugging
- **Metadata**: Flexible JSONB storage for document attributes

## Next Steps

After Supabase is configured:
1. Begin KAN-3: Document processing pipeline
2. Implement KAN-4: Primary Response Agent
3. Set up KAN-5: Approver Agent validation