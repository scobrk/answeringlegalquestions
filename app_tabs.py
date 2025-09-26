"""
NSW Revenue AI Assistant - Tabbed Interface
Chat | Response | Citations tabs with dynamic Hugging Face data integration
"""

import streamlit as st
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Optional
import json

# Load environment variables
load_dotenv()

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import local modules
from data.local_vector_store import LocalVectorStore
from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

# Page configuration
st.set_page_config(
    page_title="NSW Revenue AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for tabbed interface with shadcn-inspired design
st.markdown("""
<style>
:root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96%;
    --secondary-foreground: 222.2 84% 4.9%;
    --muted: 210 40% 96%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96%;
    --accent-foreground: 222.2 84% 4.9%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
}

.main .block-container {
    max-width: 100%;
    padding: 1rem;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    background-color: hsl(var(--secondary));
    border-radius: var(--radius);
    border: 1px solid hsl(var(--border));
    color: hsl(var(--secondary-foreground));
    font-weight: 500;
}

.stTabs [aria-selected="true"] {
    background-color: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
}

.tab-content {
    background: hsl(var(--background));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    padding: 1.5rem;
    min-height: 500px;
    margin-top: 1rem;
}

.chat-message-user {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    padding: 0.75rem;
    border-radius: var(--radius);
    margin: 0.5rem 0;
    margin-left: 2rem;
}

.chat-message-assistant {
    background: hsl(var(--secondary));
    color: hsl(var(--secondary-foreground));
    padding: 0.75rem;
    border-radius: var(--radius);
    margin: 0.5rem 0;
    margin-right: 2rem;
}

.citation-item {
    background: hsl(var(--accent));
    border: 1px solid hsl(var(--border));
    border-radius: calc(var(--radius) - 2px);
    padding: 0.75rem;
    margin: 0.5rem 0;
}

.citation-title {
    font-weight: 600;
    color: hsl(var(--foreground));
    margin-bottom: 0.5rem;
}

.citation-content {
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
    line-height: 1.4;
}

.response-container {
    background: hsl(var(--background));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    padding: 1rem;
    margin: 1rem 0;
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: calc(var(--radius) - 2px);
    font-size: 0.75rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
}

.status-success {
    background: hsl(142.1 76.2% 36.3%/10%);
    color: hsl(142.1 70.6% 45.3%);
    border: 1px solid hsl(142.1 76.2% 36.3%/20%);
}

.status-info {
    background: hsl(221.2 83.2% 53.3%/10%);
    color: hsl(221.2 83.2% 53.3%);
    border: 1px solid hsl(221.2 83.2% 53.3%/20%);
}

.status-warning {
    background: hsl(38 92% 50%/10%);
    color: hsl(38 92% 50%);
    border: 1px solid hsl(38 92% 50%/20%);
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'vector_store' not in st.session_state:
    with st.spinner("Loading NSW Revenue legislation corpus..."):
        st.session_state.vector_store = LocalVectorStore()

if 'dual_agent' not in st.session_state:
    st.session_state.dual_agent = LocalDualAgentOrchestrator()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'current_response' not in st.session_state:
    st.session_state.current_response = None

if 'current_citations' not in st.session_state:
    st.session_state.current_citations = []

if 'processing_status' not in st.session_state:
    st.session_state.processing_status = None

# Main header
st.markdown("# NSW Revenue AI Assistant")
st.markdown("**Dynamic legal assistance powered by Hugging Face Australian Legal Corpus**")

# Query input at the top
with st.container():
    query = st.text_input(
        "Ask about NSW Revenue legislation:",
        placeholder="e.g., What is the payroll tax rate in NSW?",
        key="main_query_input"
    )

    col1, col2, col3 = st.columns([1, 1, 8])

    with col1:
        if st.button("Send", type="primary", use_container_width=True):
            if query.strip():
                # Set processing status
                st.session_state.processing_status = "processing"

                # Add user message to history
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': query,
                    'timestamp': time.time()
                })

                # Process query with local vector store data
                try:
                    with st.spinner("Searching NSW Revenue legislation..."):
                        # Search local vector store for relevant documents
                        relevant_docs = st.session_state.vector_store.search(query, k=5, threshold=0.2)

                    with st.spinner("Generating AI response..."):
                        # Generate response using dual agent system
                        response = st.session_state.dual_agent.process_query(
                            query,
                            enable_approval=True
                        )

                    # Store results
                    st.session_state.current_response = response
                    st.session_state.current_citations = relevant_docs
                    st.session_state.processing_status = "completed"

                    # Add assistant response to history
                    assistant_message = response.final_response.content if hasattr(response, 'final_response') else str(response)
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': assistant_message,
                        'confidence': getattr(response.final_response, 'confidence_score', 0.0),
                        'timestamp': time.time()
                    })

                except Exception as e:
                    st.session_state.processing_status = "error"
                    st.error(f"Error processing query: {str(e)}")
                    st.session_state.current_response = None
                    st.session_state.current_citations = []

                # Clear input and rerun
                st.rerun()

    with col2:
        if st.button("Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.current_response = None
            st.session_state.current_citations = []
            st.session_state.processing_status = None
            st.rerun()

# Create tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat", "🤖 Response", "📚 Citations"])

# TAB 1: Chat History
with tab1:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)

    if st.session_state.chat_history:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f'''
                <div class="chat-message-user">
                    <strong>You:</strong> {message["content"]}
                </div>
                ''', unsafe_allow_html=True)
            else:
                confidence_info = ""
                if 'confidence' in message:
                    confidence_info = f" (Confidence: {message['confidence']:.2f})"

                st.markdown(f'''
                <div class="chat-message-assistant">
                    <strong>Assistant{confidence_info}:</strong><br>
                    {message["content"][:300]}{"..." if len(message["content"]) > 300 else ""}
                </div>
                ''', unsafe_allow_html=True)
    else:
        st.markdown("### Welcome to NSW Revenue AI Assistant")
        st.markdown("Ask questions about NSW taxation and revenue legislation.")

        st.markdown("**Sample Questions:**")
        sample_queries = [
            "What is the current payroll tax rate in NSW?",
            "How is land tax calculated for residential properties?",
            "What stamp duty concessions are available for first home buyers?",
            "What are the penalties for late payment of payroll tax?",
            "How do I apply for a land tax exemption?"
        ]

        for sample in sample_queries:
            if st.button(sample, key=f"sample_chat_{hash(sample)}", use_container_width=True):
                st.session_state.main_query_input = sample
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: AI Response
with tab2:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)

    if st.session_state.processing_status == "processing":
        st.info("Processing your query...")

    elif st.session_state.current_response:
        # Display response status
        if hasattr(st.session_state.current_response, 'approval_decision'):
            if st.session_state.current_response.approval_decision.is_approved:
                st.markdown('<span class="status-badge status-success">✓ Approved Response</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-badge status-warning">⚠ Pending Review</span>', unsafe_allow_html=True)

        # Display main response
        if hasattr(st.session_state.current_response, 'final_response'):
            response_content = st.session_state.current_response.final_response.content
            st.markdown(f'<div class="response-container">{response_content}</div>', unsafe_allow_html=True)

            # Display metadata
            col1, col2, col3 = st.columns(3)

            with col1:
                confidence = getattr(st.session_state.current_response.final_response, 'confidence_score', 0.0)
                st.metric("Confidence Score", f"{confidence:.2f}")

            with col2:
                processing_time = getattr(st.session_state.current_response, 'total_processing_time', 0.0)
                st.metric("Processing Time", f"{processing_time:.2f}s")

            with col3:
                doc_count = len(st.session_state.current_citations)
                st.metric("Source Documents", doc_count)

        else:
            st.markdown(f'<div class="response-container">{str(st.session_state.current_response)}</div>', unsafe_allow_html=True)

    elif st.session_state.processing_status == "error":
        st.error("An error occurred while processing your query. Please try again.")

    else:
        st.markdown("### AI Response Panel")
        st.markdown("Responses from the dual-agent system will appear here.")
        st.markdown("**Features:**")
        st.markdown("- Primary response generation from legal corpus")
        st.markdown("- Secondary approval and validation")
        st.markdown("- Confidence scoring and metadata")
        st.markdown("- Dynamic interpretation of legislation")

    st.markdown('</div>', unsafe_allow_html=True)

# TAB 3: Citations and References
with tab3:
    st.markdown('<div class="tab-content">', unsafe_allow_html=True)

    if st.session_state.current_citations:
        st.markdown("### Source Documents from Australian Legal Corpus")

        for i, citation in enumerate(st.session_state.current_citations, 1):
            # Extract key information
            title = citation.get('title', 'Unknown Document')
            content_preview = citation.get('content', '')[:300] + "..." if len(citation.get('content', '')) > 300 else citation.get('content', '')
            similarity_score = citation.get('similarity_score', 0.0)
            jurisdiction = citation.get('jurisdiction', 'Unknown')

            st.markdown(f'''
            <div class="citation-item">
                <div class="citation-title">{i}. {title}</div>
                <div class="citation-content">
                    <strong>Jurisdiction:</strong> {jurisdiction}<br>
                    <strong>Relevance Score:</strong> {similarity_score:.3f}<br>
                    <strong>Content:</strong> {content_preview}
                </div>
            </div>
            ''', unsafe_allow_html=True)

        # Display citation summary
        st.markdown("---")
        nsw_docs = [doc for doc in st.session_state.current_citations if 'nsw' in doc.get('jurisdiction', '').lower()]
        revenue_docs = [doc for doc in st.session_state.current_citations if any(term in doc.get('title', '').lower() for term in ['tax', 'duty', 'revenue', 'payroll', 'land'])]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", len(st.session_state.current_citations))
        with col2:
            st.metric("NSW Documents", len(nsw_docs))
        with col3:
            st.metric("Revenue Related", len(revenue_docs))

    else:
        st.markdown("### Citations & References Panel")
        st.markdown("Source documents and legal references will appear here.")

        # Show available corpus info
        try:
            available_acts = st.session_state.vector_store.list_available_acts()
            st.markdown("**Available NSW Revenue Acts:**")
            for act in available_acts:
                act_display = act.replace('_', ' ').title()
                st.markdown(f"• {act_display}")
        except Exception:
            st.markdown("**Legal Corpus:** NSW Revenue Legislation")
            st.markdown("- Duties Act 1997")
            st.markdown("- Payroll Tax Act 2007")
            st.markdown("- Land Tax Act 1956")
            st.markdown("- Revenue Administration Act 1996")

    st.markdown('</div>', unsafe_allow_html=True)

# Footer with system status
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    try:
        acts_count = len(st.session_state.vector_store.list_available_acts())
        st.success(f"Corpus: {acts_count} Acts")
    except Exception:
        st.info("Corpus: Loading...")

with col2:
    st.info("Dual Agents: Active")

with col3:
    st.info("Model: GPT-3.5 Turbo")

with col4:
    if st.session_state.processing_status:
        status_color = {"processing": "🟡", "completed": "🟢", "error": "🔴"}
        st.write(f"{status_color.get(st.session_state.processing_status, '⚪')} {st.session_state.processing_status.title()}")
    else:
        st.write("⚪ Ready")