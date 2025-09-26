"""
NSW Revenue AI Assistant - Dynamic Context-Driven Interface
Real-time content retrieval and processing from multiple sources
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
from data.dynamic_context_layer import DynamicContextLayer, ContextDocument
from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

# Page configuration
st.set_page_config(
    page_title="NSW Revenue AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for dynamic interface
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
    --border: 214.3 31.8% 91.4%;
    --radius: 0.5rem;
}

.main .block-container {
    max-width: 100%;
    padding: 1rem;
}

.dynamic-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: calc(var(--radius) - 2px);
    font-size: 0.75rem;
    font-weight: 500;
    margin: 0.25rem 0.25rem 0.25rem 0;
}

.source-web {
    background: hsl(142.1 76.2% 36.3%/10%);
    color: hsl(142.1 70.6% 45.3%);
    border: 1px solid hsl(142.1 76.2% 36.3%/20%);
}

.source-hf {
    background: hsl(221.2 83.2% 53.3%/10%);
    color: hsl(221.2 83.2% 53.3%);
    border: 1px solid hsl(221.2 83.2% 53.3%/20%);
}

.source-local {
    background: hsl(38 92% 50%/10%);
    color: hsl(38 92% 50%);
    border: 1px solid hsl(38 92% 50%/20%);
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

.context-card {
    background: hsl(var(--accent));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    padding: 1rem;
    margin: 0.5rem 0;
}

.context-header {
    font-weight: 600;
    color: hsl(var(--foreground));
    margin-bottom: 0.5rem;
}

.context-content {
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
    line-height: 1.4;
}

.relevance-score {
    font-weight: 500;
    color: hsl(var(--primary));
}

.processing-info {
    background: hsl(var(--muted));
    border-radius: var(--radius);
    padding: 0.75rem;
    margin: 0.5rem 0;
    font-size: 0.875rem;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'context_layer' not in st.session_state:
    with st.spinner("Initializing dynamic context layer..."):
        st.session_state.context_layer = DynamicContextLayer()

if 'dual_agent' not in st.session_state:
    st.session_state.dual_agent = LocalDualAgentOrchestrator()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'current_response' not in st.session_state:
    st.session_state.current_response = None

if 'current_context' not in st.session_state:
    st.session_state.current_context = []

if 'processing_info' not in st.session_state:
    st.session_state.processing_info = {}

# Main header
st.markdown("# NSW Revenue AI Assistant")
st.markdown("**Dynamic context retrieval from NSW Revenue website, Hugging Face corpus, and local legislation**")

# Query input
with st.container():
    query = st.text_input(
        "Ask about NSW Revenue legislation:",
        placeholder="e.g., What is the current payroll tax rate and threshold?",
        key="main_query_input"
    )

    col1, col2, col3 = st.columns([1, 1, 8])

    with col1:
        if st.button("Ask", type="primary", use_container_width=True):
            if query.strip():
                # Clear previous results
                st.session_state.current_response = None
                st.session_state.current_context = []
                st.session_state.processing_info = {}

                # Add user message to history
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': query,
                    'timestamp': time.time()
                })

                # Process with progress tracking
                with st.spinner("Retrieving relevant context..."):
                    start_time = time.time()
                    context_docs = st.session_state.context_layer.get_relevant_context(query, max_docs=5)
                    context_time = time.time() - start_time

                    st.session_state.current_context = context_docs
                    st.session_state.processing_info['context_retrieval_time'] = context_time
                    st.session_state.processing_info['context_sources'] = {}

                    # Count sources
                    for doc in context_docs:
                        source = doc.source
                        st.session_state.processing_info['context_sources'][source] = \
                            st.session_state.processing_info['context_sources'].get(source, 0) + 1

                with st.spinner("Generating AI response..."):
                    try:
                        response_start = time.time()
                        response = st.session_state.dual_agent.process_query(query, enable_approval=True)
                        response_time = time.time() - response_start

                        st.session_state.current_response = response
                        st.session_state.processing_info['response_time'] = response_time
                        st.session_state.processing_info['total_time'] = context_time + response_time

                        # Add assistant response to history
                        assistant_message = response.final_response.content if hasattr(response, 'final_response') else str(response)
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': assistant_message,
                            'confidence': getattr(response.final_response, 'confidence_score', 0.0),
                            'timestamp': time.time()
                        })

                    except Exception as e:
                        st.error(f"Error generating response: {str(e)}")

                st.rerun()

    with col2:
        if st.button("Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.current_response = None
            st.session_state.current_context = []
            st.session_state.processing_info = {}
            st.rerun()

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "🤖 AI Response", "🔍 Context Sources", "📊 Processing Info"])

# TAB 1: Chat History
with tab1:
    if st.session_state.chat_history:
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f"**You:** {message['content']}")
            else:
                confidence_info = ""
                if 'confidence' in message:
                    confidence_info = f" (Confidence: {message['confidence']:.2f})"

                st.markdown(f"**Assistant{confidence_info}:**")
                st.markdown(message['content'][:500] + ("..." if len(message['content']) > 500 else ""))
                st.markdown("---")
    else:
        st.markdown("### Welcome to NSW Revenue AI Assistant")
        st.markdown("This system dynamically retrieves context from:")
        st.markdown("🌐 **NSW Revenue Website** - Live legislation and rulings")
        st.markdown("🤗 **Hugging Face Corpus** - Australian Legal Corpus")
        st.markdown("📁 **Local Content** - Cached NSW Revenue acts")

        st.markdown("### Sample Questions:")
        samples = [
            "What is the current payroll tax rate and threshold in NSW?",
            "How do I calculate land tax for a $2 million property?",
            "What stamp duty concessions are available for first home buyers?",
            "What are the penalties for late payroll tax payments?",
            "How do I apply for a land tax exemption?"
        ]

        for sample in samples:
            if st.button(sample, key=f"sample_{hash(sample)}", use_container_width=True):
                st.session_state.main_query_input = sample
                st.rerun()

# TAB 2: AI Response
with tab2:
    if st.session_state.current_response:
        # Display response status
        if hasattr(st.session_state.current_response, 'approval_decision'):
            if st.session_state.current_response.approval_decision.is_approved:
                st.success("✓ Response Approved")
            else:
                st.warning("⚠ Response Pending Review")

        # Display main response
        if hasattr(st.session_state.current_response, 'final_response'):
            st.markdown("### AI Response")
            st.markdown(st.session_state.current_response.final_response.content)

            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                confidence = getattr(st.session_state.current_response.final_response, 'confidence_score', 0.0)
                st.metric("Confidence", f"{confidence:.2f}")
            with col2:
                processing_time = getattr(st.session_state.current_response, 'total_processing_time', 0.0)
                st.metric("Processing Time", f"{processing_time:.2f}s")
            with col3:
                citation_count = len(getattr(st.session_state.current_response.final_response, 'citations', []))
                st.metric("Citations", citation_count)

        else:
            st.markdown(str(st.session_state.current_response))
    else:
        st.markdown("### AI Response Panel")
        st.info("Ask a question to see the AI response here")

# TAB 3: Context Sources
with tab3:
    if st.session_state.current_context:
        st.markdown("### Retrieved Context Documents")

        for i, doc in enumerate(st.session_state.current_context, 1):
            # Source badge
            source_class = {
                'nsw_revenue_web': 'source-web',
                'huggingface': 'source-hf',
                'local': 'source-local'
            }.get(doc.source, 'source-local')

            st.markdown(f'''
            <div class="context-card">
                <div class="context-header">
                    {i}. {doc.title}
                    <span class="dynamic-badge {source_class}">{doc.source.replace('_', ' ').title()}</span>
                </div>
                <div class="context-content">
                    <strong>Relevance Score:</strong> <span class="relevance-score">{doc.relevance_score:.3f}</span><br>
                    <strong>Content:</strong> {doc.content[:300]}{"..." if len(doc.content) > 300 else ""}
                </div>
            </div>
            ''', unsafe_allow_html=True)

        # Context summary
        st.markdown("### Context Summary")
        summary = st.session_state.context_layer.get_context_summary(st.session_state.current_context)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", summary['total_docs'])
        with col2:
            st.metric("Avg Relevance", f"{summary['avg_relevance']:.3f}")
        with col3:
            st.metric("Top Relevance", f"{summary['top_relevance']:.3f}")

        if summary['sources']:
            st.markdown("**Sources Found:**")
            for source, count in summary['sources'].items():
                st.markdown(f"• {source.replace('_', ' ').title()}: {count} documents")

    else:
        st.markdown("### Context Sources Panel")
        st.info("Context documents retrieved for your query will appear here")

# TAB 4: Processing Information
with tab4:
    if st.session_state.processing_info:
        st.markdown("### Processing Performance")

        col1, col2, col3 = st.columns(3)
        with col1:
            context_time = st.session_state.processing_info.get('context_retrieval_time', 0)
            st.metric("Context Retrieval", f"{context_time:.2f}s")
        with col2:
            response_time = st.session_state.processing_info.get('response_time', 0)
            st.metric("Response Generation", f"{response_time:.2f}s")
        with col3:
            total_time = st.session_state.processing_info.get('total_time', 0)
            st.metric("Total Time", f"{total_time:.2f}s")

        st.markdown("### Source Breakdown")
        sources = st.session_state.processing_info.get('context_sources', {})
        if sources:
            for source, count in sources.items():
                source_display = source.replace('_', ' ').title()
                st.markdown(f"• **{source_display}**: {count} documents retrieved")
        else:
            st.info("No source breakdown available")

        if st.session_state.current_response and hasattr(st.session_state.current_response, 'approval_decision'):
            st.markdown("### Approval Process")
            approval = st.session_state.current_response.approval_decision
            st.markdown(f"**Status:** {approval.feedback}")
            if approval.review_notes:
                st.markdown("**Review Notes:**")
                for note in approval.review_notes:
                    st.markdown(f"• {note}")

    else:
        st.markdown("### Processing Information Panel")
        st.info("Processing performance metrics will appear here")

# Footer
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.success("Dynamic Context: Active")

with col2:
    st.info("Dual Agents: Enabled")

with col3:
    st.info("Multi-Source: NSW + HF + Local")

with col4:
    if st.session_state.processing_info:
        total_time = st.session_state.processing_info.get('total_time', 0)
        if total_time > 0:
            st.metric("Last Query", f"{total_time:.1f}s")
        else:
            st.write("⚪ Ready")
    else:
        st.write("⚪ Ready")