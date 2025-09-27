# Primary Response Agent Architecture (KAN-4)

## **ARCHITECT AGENT DESIGN**

### **Integration with Existing Components**
```
User Query → Primary Response Agent → Supabase Vector Search → Processed Documents (KAN-3)
    ↓               ↓                      ↓                         ↓
Query Type → Document Retrieval → Context Building → LLM Response → Structured Output
```

### **Core Architecture Components**

#### **1. Query Classification System**
```python
QueryClassifier → Revenue Query Types:
├── payroll_tax: "Payroll tax calculations, thresholds, rates"
├── land_tax: "Land tax assessments, exemptions, valuations"
├── duties: "Stamp duty calculations, conveyance rates"
├── fines: "Penalty inquiries, enforcement, appeals"
├── grants: "Grant eligibility, first home buyers"
├── administration: "Revenue administration, reviews, assessments"
└── general: "Other revenue-related queries"
```

#### **2. Document Retrieval Pipeline**
```python
DocumentRetriever → Supabase Integration:
├── Vector Search: pgvector similarity search with embeddings
├── Metadata Filtering: Act type, section, jurisdiction filtering
├── Context Assembly: Chunk ranking and relevance scoring
└── Citation Tracking: Source document references
```

#### **3. Response Generation Engine**
```python
ResponseGenerator → LLM Integration:
├── Context Building: Assembled document chunks with metadata
├── Prompt Engineering: NSW Revenue legislation expert prompts
├── Citation Extraction: Automatic legal reference parsing
└── Confidence Scoring: Document relevance + LLM certainty
```

### **Integration Points with KAN-3**

#### **Document Pipeline Connection**
- **Input**: Processed NSW documents from KAN-3 pipeline
- **Storage**: Supabase tables (documents, document_chunks)
- **Embeddings**: OpenAI text-embedding-3-small vectors
- **Metadata**: Act names, sections, keywords from NSW filter

#### **RAGflow Integration**
- **Chunked Content**: 512 token chunks with 50 token overlap
- **Legal Context**: Section headers preserved in chunks
- **Metadata Enrichment**: NSW-specific legislative structure

### **Response Structure**

```python
PrimaryResponse = {
    "answer": str,                    # Direct answer to user query
    "citations": List[str],           # Legal references (e.g., "Duties Act 1997 s31")
    "confidence": float,              # Combined confidence score (0.0-1.0)
    "query_type": str,                # Classified query category
    "source_documents": List[dict],   # Retrieved document chunks
    "calculations": Optional[dict],   # Step-by-step calculations if applicable
    "assumptions": List[str],         # Any assumptions made in response
    "limitations": List[str],         # Information gaps or uncertainties
    "timestamp": datetime,            # Response generation time
    "processing_time": float          # Time taken to generate response
}
```

### **Performance Targets (from KAN-4)**
- **Response Time**: <3 seconds end-to-end
- **Accuracy**: >95% for factual information
- **Citation Precision**: 100% valid legal references
- **Confidence Alignment**: Score correlates with actual accuracy
- **Error Handling**: Graceful degradation for edge cases

### **Quality Assurance Strategy**

#### **Input Validation**
- Query length limits (10-500 words)
- Content filtering for appropriate legal queries
- Rate limiting to prevent abuse

#### **Output Validation**
- Citation format verification
- Legal reference existence checking
- Response coherence scoring
- Confidence threshold enforcement

### **Error Handling Patterns**

```python
ErrorResponse = {
    "error_type": str,                # Classification of error
    "message": str,                   # User-friendly error message
    "suggestions": List[str],         # Alternative query suggestions
    "fallback_response": Optional[str], # Basic response if available
    "technical_details": Optional[dict] # Debug info (dev mode only)
}
```

### **MVP Scope Compliance**

#### **✅ Included Features**
- NSW Revenue legislation focus only
- Basic query classification (7 types)
- Vector similarity search
- Citation extraction
- Confidence scoring
- Error handling

#### **❌ Excluded Features**
- Multi-jurisdiction support
- Advanced ML query understanding
- Real-time legislation updates
- Complex calculation engines
- Natural language generation training

### **Technical Dependencies**

#### **External Services**
- **OpenAI API**: GPT-3.5-turbo-16k for response generation
- **OpenAI API**: text-embedding-3-small for query embeddings
- **Supabase**: PostgreSQL with pgvector for document storage/search

#### **Internal Components**
- **KAN-3 Pipeline**: Document processing and chunking
- **NSW Filter**: Legal document metadata and classification
- **Web Hosting**: Railway backend deployment capability

### **Data Flow Architecture**

```
1. User Query Input
   ↓
2. Query Classification (7 revenue types)
   ↓
3. Query Embedding Generation (OpenAI)
   ↓
4. Vector Similarity Search (Supabase pgvector)
   ↓
5. Document Chunk Retrieval (Top 5 most relevant)
   ↓
6. Context Assembly (Chunks + metadata)
   ↓
7. LLM Prompt Construction (NSW Revenue expert)
   ↓
8. Response Generation (GPT-3.5-turbo-16k)
   ↓
9. Citation Extraction (Regex + validation)
   ↓
10. Confidence Scoring (Combined metrics)
    ↓
11. Structured Response Output
```

### **Monitoring & Observability**

#### **Key Metrics**
- Query processing time per stage
- Document retrieval relevance scores
- LLM response quality metrics
- Citation accuracy rates
- Error rates by query type

#### **Logging Strategy**
- All queries logged to Supabase audit tables
- Processing time breakdowns
- Document retrieval statistics
- Error details and stack traces

## **Implementation Phases**

### **Phase 1**: Core Infrastructure
- Supabase vector search integration
- Query classification system
- Basic document retrieval

### **Phase 2**: Response Generation
- LLM integration and prompt engineering
- Citation extraction system
- Confidence scoring algorithm

### **Phase 3**: Quality & Performance
- Error handling and validation
- Performance optimization
- Comprehensive testing

This architecture ensures seamless integration with our existing KAN-3 document processing pipeline while maintaining MVP scope and zero-cost infrastructure constraints.