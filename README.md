# Revenue NSW AI Assistant

An AI-powered legislative query system for Revenue NSW staff using dual-agent validation approach.

## Quick Start

1. Copy environment variables:
```bash
cp .env.example .env
# Edit .env with your actual values
```

2. Start the development environment:
```bash
cd docker
docker-compose up -d
```

3. Access the application:
- Frontend (Streamlit): http://localhost:8501
- Backend (FastAPI): http://localhost:8000
- RAGflow: http://localhost:8080

## Project Structure

```
/
├── app/                 # FastAPI backend (KAN-4, KAN-5, KAN-8)
├── docker/             # Docker configurations (KAN-2)
├── data/               # Document processing (KAN-3)
├── agents/             # Primary & Approver agents (KAN-4, KAN-5)
├── ui/                 # Streamlit interface (KAN-6)
├── tests/              # Testing framework (KAN-7)
├── monitoring/         # Audit & logging (KAN-8)
└── docs/               # Documentation
```

## Development Workflow

**IMPORTANT**: Always reference Jira items (KAN-1 through KAN-8) when working on tasks.

### Jira Task Structure
- **KAN-1**: Epic - Revenue NSW Staff Assistant
- **KAN-2**: Docker environment setup ✅
- **KAN-3**: Legal document processing pipeline
- **KAN-4**: Primary Response Agent with RAG
- **KAN-5**: Approver Agent for validation
- **KAN-6**: Streamlit UI development
- **KAN-7**: Testing framework
- **KAN-8**: Audit logging and monitoring

## Technology Stack

- **Database**: Supabase PostgreSQL with pgvector (free tier)
- **Document Processing**: RAGflow
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **LLM**: OpenAI GPT-3.5-turbo
- **Data Source**: [Australian Legal Corpus](https://huggingface.co/datasets/isaacus/open-australian-legal-corpus)

## Contributing

1. Always start work by referencing the relevant Jira item
2. Update Jira progress as work advances
3. Follow the MVP scope (see CLAUDE.md)
4. Test incrementally
5. Link commits to Jira items# Deployment trigger: Sat 27 Sep 2025 09:46:26 AEST
