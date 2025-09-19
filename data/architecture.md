# Document Processing Architecture (KAN-3)

## **ARCHITECT AGENT DESIGN**

### **Overall Data Flow**
```
Hugging Face Dataset → NSW Filter → RAGflow Processing → Document Parser → Supabase Storage
     (229K docs)      (NSW only)     (chunking)        (metadata)      (pgvector)
```

### **Core Architecture Components**

#### 1. **Dataset Ingestion Layer**
```python
HuggingFaceConnector → NSWLegislationFilter → DocumentBatch
```

#### 2. **RAGflow Processing Layer**
```python
RAGflowClient → SemanticChunker → MetadataExtractor
```

#### 3. **Supabase Storage Layer**
```python
EmbeddingGenerator → SupabaseConnector → VectorIndexer
```

### **Key Architectural Decisions**

#### **Decision 1: Hybrid Processing Approach**
- **RAGflow**: Advanced document understanding and chunking
- **Custom Pipeline**: NSW-specific filtering and metadata extraction
- **Supabase**: Vector storage and retrieval with pgvector

#### **Decision 2: Two-Stage Processing**
1. **Stage 1**: Bulk NSW filtering and initial processing
2. **Stage 2**: RAGflow chunking and Supabase embedding storage

#### **Decision 3: Zero-Cost Optimization**
- Process in batches to stay within free tier limits
- Cache intermediate results locally
- Use Supabase batch operations for efficiency

### **Priority NSW Legislation (from KAN-3)**
1. Duties Act 1997 (NSW) - Stamp duty regulations
2. Payroll Tax Act 2007 (NSW) - Payroll tax calculations
3. Land Tax Act 1956 (NSW) - Land tax assessments
4. Land Tax Management Act 1956 (NSW) - Land tax administration
5. Revenue Administration Act 1996 (NSW) - General revenue procedures

### **Document Processing Strategy**

#### **Chunking Parameters (per KAN-3)**
- **Chunk Size**: 512 tokens
- **Overlap**: 50 tokens
- **Boundary Preservation**: Section and paragraph integrity
- **Context Inclusion**: Section headers in each chunk

#### **Metadata Schema**
```python
{
    "act_name": str,           # e.g., "Duties Act 1997"
    "act_number": str,         # e.g., "1997 No 123"
    "section": str,            # e.g., "31", "31A"
    "subsection": str,         # e.g., "(1)", "(a)(i)"
    "effective_date": date,    # When section became effective
    "last_amended": date,      # Last amendment date
    "keywords": List[str],     # Extracted legal terms
    "document_type": str,      # "act", "regulation", "rule"
    "jurisdiction": str        # Always "NSW" for our filter
}
```

### **Integration Points**

#### **RAGflow Integration**
- **Input**: Filtered NSW documents from Hugging Face
- **Processing**: Advanced legal document understanding
- **Output**: Semantically chunked sections with context preservation

#### **Supabase Integration**
- **Input**: Processed chunks from RAGflow
- **Storage**: Documents, chunks, and embeddings tables
- **Indexing**: pgvector similarity search optimization

### **Error Handling & Validation**
- **Document Format Validation**: PDF, XML, TXT support
- **Legal Structure Validation**: Proper section numbering
- **Metadata Completeness**: Required fields populated
- **Chunk Quality**: Minimum token thresholds

### **Performance Targets**
- **Processing Speed**: 100 documents/hour
- **Accuracy**: >95% metadata extraction
- **Storage Efficiency**: <1GB total in Supabase free tier
- **Retrieval Speed**: <2 seconds for similarity search

## **Next Implementation Steps**
1. **Data Engineering Agent**: Hugging Face dataset integration
2. **Backend Agent**: NSW filtering and validation logic
3. **Data Engineering Agent**: RAGflow chunking pipeline
4. **DevOps Agent**: Monitoring and error handling