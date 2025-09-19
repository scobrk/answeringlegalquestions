# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Revenue NSW AI Assistant** - AI-powered legislative query system for Revenue NSW staff using dual-agent validation approach.

**Jira Project**: answeringlegalquestions.atlassian.net (KAN board)

## CRITICAL WORKFLOW REQUIREMENTS

### **Jira-First Development**
1. **ALWAYS start work by referencing the relevant Jira item** (KAN-1 through KAN-8)
2. **Update Jira progress** as work advances through tasks
3. **Link all commits to Jira items** for complete traceability
4. **Complete Jira tasks** before moving to next items

### **Jira Task Structure**
- **KAN-1**: Epic - Revenue NSW Staff Assistant (main project)
- **KAN-2**: Docker environment and docker-compose configuration
- **KAN-3**: Legal document processing and chunking pipeline
- **KAN-4**: Primary Response Agent with RAG pipeline
- **KAN-5**: Approver Agent for response validation
- **KAN-6**: Streamlit UI for staff interface
- **KAN-7**: Comprehensive testing framework
- **KAN-8**: Audit logging and monitoring system

## Technology Stack

### **Zero-Cost Architecture**
- **Database**: Supabase PostgreSQL with pgvector (free tier)
- **Document Processing**: RAGflow (self-hosted container)
- **Backend**: FastAPI with Supabase integration
- **Frontend**: Streamlit (no authentication required)
- **Vector Search**: pgvector extension in Supabase
- **Storage**: Supabase Storage for document cache
- **Deployment**: Railway/Render free tiers
- **LLM**: OpenAI GPT-3.5-turbo (pay-per-use only)
- **Embeddings**: OpenAI text-embedding-3-small

### **Data Sources**
- **Primary Dataset**: https://huggingface.co/datasets/isaacus/open-australian-legal-corpus
- **RAGflow Repository**: https://github.com/infiniflow/ragflow

## Architecture

### **Dual-Agent System**
1. **Primary Response Agent**: Generates initial responses using RAG pipeline
2. **Approver Agent**: Validates responses for accuracy and completeness
3. **Document Processing**: RAGflow handles NSW legislation parsing and chunking
4. **Vector Storage**: Supabase pgvector for semantic search

### **Directory Structure**
```
/
├── app/                 # Main application code
├── docker/             # Docker configurations (KAN-2)
├── data/               # Document processing (KAN-3)
├── agents/             # Primary & Approver agents (KAN-4, KAN-5)
├── ui/                 # Streamlit interface (KAN-6)
├── tests/              # Testing framework (KAN-7)
├── monitoring/         # Audit & logging (KAN-8)
└── docs/               # Documentation
```

## Development Workflow

### **Setup Commands**
```bash
# Install MCPs (start with Supabase)
# Docker environment setup (KAN-2)
docker-compose up -d

# Install dependencies
pip install -r requirements.txt

# Run application
streamlit run ui/main.py
```

## Constraints & Boundaries

### **MVP Scope (8-week timeline)**
- ✅ Dual-agent question answering
- ✅ NSW Revenue legislation focus
- ✅ Basic Streamlit interface
- ✅ Audit logging
- ✅ Zero infrastructure cost
- ❌ Authentication system
- ❌ Custom model training
- ❌ Advanced analytics
- ❌ Mobile applications

### **Success Metrics**
- **Accuracy**: >98% post-validation
- **Response Time**: <10 seconds end-to-end
- **Validation Pass Rate**: >85%
- **Infrastructure Cost**: $0 (only OpenAI API usage)

## Notes for Development

- **Always reference Jira items** when starting work
- **Update Jira status** as tasks progress
- **Focus on MVP delivery** within 8-week timeline
- **Prioritize zero-cost solutions** using free tiers
- **Test incrementally** following KAN-7 framework
- **Document all decisions** in this file