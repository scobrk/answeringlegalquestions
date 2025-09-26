# NSW Revenue AI Assistant - Architecture Diagrams

## System Architecture Overview

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Web Interface - FastAPI]
        CLI[CLI Interface]
    end

    subgraph "API Layer"
        API[FastAPI Server]
        Health[Health Check]
    end

    subgraph "Core Processing Engine"
        Orchestrator[Dual Agent Orchestrator]
        ClassAgent[Classification Agent]
        SourcingAgent[Targeted Sourcing Agent]
        PrimaryAgent[Primary Agent]
        SecondaryAgent[Secondary Agent]
        ApprovalAgent[Approval Agent]
    end

    subgraph "Data Layer"
        FAISS[FAISS Vector Store]
        LocalDocs[Local NSW Legislation]
        NSWWeb[NSW Revenue Website]
        HuggingFace[HuggingFace Legal Corpus]
    end

    subgraph "External Services"
        OpenAI[OpenAI GPT-3.5-turbo]
    end

    UI --> API
    CLI --> Orchestrator
    API --> Orchestrator

    Orchestrator --> ClassAgent
    Orchestrator --> SourcingAgent
    Orchestrator --> PrimaryAgent
    Orchestrator --> SecondaryAgent
    Orchestrator --> ApprovalAgent

    ClassAgent --> OpenAI
    PrimaryAgent --> OpenAI
    SecondaryAgent --> OpenAI

    SourcingAgent --> FAISS
    SourcingAgent --> LocalDocs
    SourcingAgent --> NSWWeb
    SourcingAgent --> HuggingFace

    API --> Health
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant FastAPI
    participant Orchestrator
    participant ClassAgent
    participant SourcingAgent
    participant PrimaryAgent
    participant ApprovalAgent
    participant OpenAI
    participant DataSources

    User->>FastAPI: Submit Query
    FastAPI->>Orchestrator: Process Query Request

    Orchestrator->>ClassAgent: Classify Question
    ClassAgent->>OpenAI: LLM Classification
    OpenAI-->>ClassAgent: Classification Result
    ClassAgent-->>Orchestrator: Revenue Type + Intent + Multi-tax

    Orchestrator->>SourcingAgent: Get Relevant Documents
    SourcingAgent->>DataSources: Vector Search + Filtering
    DataSources-->>SourcingAgent: Relevant Documents
    SourcingAgent-->>Orchestrator: Ranked Document Set

    Orchestrator->>PrimaryAgent: Generate Response
    PrimaryAgent->>OpenAI: LLM Generation with Context
    OpenAI-->>PrimaryAgent: Generated Response
    PrimaryAgent-->>Orchestrator: Response + Citations

    Orchestrator->>ApprovalAgent: Evaluate Quality
    ApprovalAgent-->>Orchestrator: Approval Decision

    Orchestrator-->>FastAPI: Final Response
    FastAPI-->>User: Formatted Answer + Citations
```

## RAG Implementation Flow

```mermaid
graph TD
    A[User Query] --> B[Question Classification]

    B --> C{Multi-tax Query?}
    C -->|Yes| D[Multi-tax Classification]
    C -->|No| E[Single-tax Classification]

    D --> F[Enhanced Multi-tax Prompting]
    E --> G[Standard Prompting]

    F --> H[Document Retrieval]
    G --> H

    H --> I[FAISS Vector Search]
    H --> J[Revenue Type Filtering]
    H --> K[Source Diversity]

    I --> L[Context Assembly]
    J --> L
    K --> L

    L --> M[LLM Generation]
    M --> N[Response Validation]

    N --> O{Quality Check}
    O -->|Pass| P[Approved Response]
    O -->|Fail| Q[Review Required]

    P --> R[Formatted Output]
    Q --> S[Human Review]
    S --> R
```

## Multi-Agent Coordination

```mermaid
graph LR
    subgraph "Agent Pipeline"
        A[Classification Agent] --> B[Targeted Sourcing Agent]
        B --> C[Primary Agent]
        C --> D[Secondary Agent]
        D --> E[Approval Agent]
    end

    subgraph "Classification Output"
        A --> F[Revenue Type]
        A --> G[Question Intent]
        A --> H[Multi-tax Detection]
        A --> I[Confidence Score]
    end

    subgraph "Sourcing Output"
        B --> J[Relevant Documents]
        B --> K[Legislative Sections]
        B --> L[Similarity Scores]
    end

    subgraph "Generation Output"
        C --> M[Initial Response]
        D --> N[Enhanced Response]
        E --> O[Approval Decision]
    end

    F --> B
    G --> B
    H --> C
    I --> E

    J --> C
    K --> C
    L --> E

    M --> D
    N --> E
```

## Component Interaction Matrix

```mermaid
graph TB
    subgraph "Data Sources"
        DS1[NSW Legislation Files]
        DS2[NSW Revenue Website]
        DS3[HuggingFace Corpus]
        DS4[FAISS Vector Index]
    end

    subgraph "Processing Components"
        PC1[Classification Agent]
        PC2[Sourcing Agent]
        PC3[Primary Agent]
        PC4[Approval Agent]
    end

    subgraph "Output Components"
        OC1[Response Formatter]
        OC2[Citation Builder]
        OC3[UI Renderer]
    end

    DS1 --> DS4
    DS2 --> PC2
    DS3 --> DS4
    DS4 --> PC2

    PC1 --> PC2
    PC2 --> PC3
    PC3 --> PC4

    PC3 --> OC1
    PC3 --> OC2
    PC4 --> OC1

    OC1 --> OC3
    OC2 --> OC3
```

## Multi-Tax Processing Flow

```mermaid
flowchart TD
    A[Complex Query Input] --> B[LLM Classification]

    B --> C{Multi-tax Detected?}
    C -->|No| D[Single Tax Processing]
    C -->|Yes| E[Extract All Tax Types]

    E --> F[Payroll Tax Analysis]
    E --> G[Land Tax Analysis]
    E --> H[Parking Levy Analysis]
    E --> I[Stamp Duty Analysis]

    F --> J[Individual Calculations]
    G --> J
    H --> J
    I --> J

    J --> K[Combine Results]
    K --> L[Total Revenue Calculation]
    L --> M[Comprehensive Response]

    D --> N[Single Tax Response]
    M --> O[Quality Validation]
    N --> O

    O --> P[Final Output with Citations]
```

## Error Handling and Validation Flow

```mermaid
graph TD
    A[Response Generated] --> B[Confidence Check]

    B --> C{Confidence > 70%?}
    C -->|No| D[Flag for Review]
    C -->|Yes| E[Citation Validation]

    E --> F{Valid Citations?}
    F -->|No| G[Missing Citations Error]
    F -->|Yes| H[Completeness Check]

    H --> I{All Components Addressed?}
    I -->|No| J[Incomplete Response Error]
    I -->|Yes| K[Calculation Validation]

    K --> L{Calculations Correct?}
    L -->|No| M[Calculation Error]
    L -->|Yes| N[Approved Response]

    D --> O[Human Review Required]
    G --> O
    J --> O
    M --> O

    O --> P[Review and Correction]
    P --> A

    N --> Q[Response Output]
```

## System Performance Monitoring

```mermaid
graph LR
    subgraph "Performance Metrics"
        PM1[Classification Time: ~0.5-1.0s]
        PM2[Document Retrieval: ~1.0-2.0s]
        PM3[Response Generation: ~2.0-4.0s]
        PM4[Total Processing: ~4.0-7.0s]
    end

    subgraph "Quality Metrics"
        QM1[Classification Accuracy: 85%+]
        QM2[Multi-tax Detection: 95%+]
        QM3[Citation Relevance: 90%+]
        QM4[Response Completeness: 92%+]
    end

    subgraph "System Health"
        SH1[API Response Time]
        SH2[Error Rate]
        SH3[Throughput]
        SH4[Resource Usage]
    end
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        LB[Load Balancer]
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance 3]
    end

    subgraph "Data Layer"
        VDB[Vector Database]
        Cache[Redis Cache]
        FS[File Storage]
    end

    subgraph "External Services"
        OpenAI[OpenAI API]
        NSW[NSW Revenue API]
    end

    subgraph "Monitoring"
        Logs[Centralized Logging]
        Metrics[Metrics Collection]
        Alerts[Alert Manager]
    end

    LB --> API1
    LB --> API2
    LB --> API3

    API1 --> VDB
    API1 --> Cache
    API1 --> FS

    API1 --> OpenAI
    API1 --> NSW

    API1 --> Logs
    API1 --> Metrics

    Metrics --> Alerts
```

## Future Enhancement Architecture

```mermaid
graph TB
    subgraph "Enhanced Data Sources"
        ATO[ATO Integration]
        Courts[Court Decisions]
        Policy[Policy Updates]
        Historical[Historical Data]
    end

    subgraph "Advanced Processing"
        Ensemble[Ensemble Models]
        FineTuned[Fine-tuned Models]
        RealTime[Real-time Updates]
    end

    subgraph "Enhanced Interface"
        Forms[Interactive Forms]
        Upload[Document Upload]
        Mobile[Mobile App]
        API[Public API]
    end

    subgraph "Enterprise Features"
        Auth[Authentication]
        Audit[Audit Trail]
        Analytics[Usage Analytics]
        Workflow[Approval Workflows]
    end

    ATO --> Ensemble
    Courts --> FineTuned
    Policy --> RealTime

    Ensemble --> Forms
    FineTuned --> Upload
    RealTime --> Mobile

    Forms --> Auth
    Upload --> Audit
    Mobile --> Analytics
    API --> Workflow
```