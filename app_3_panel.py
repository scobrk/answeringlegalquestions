"""
NSW Revenue AI Assistant - 3-Panel Chat Interface
Left: Chat Input | Center: AI Response | Right: Citations/References
"""

import streamlit as st
import os
import sys
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

# Custom CSS for 3-panel layout with shadcn-inspired design
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

.panel {
    background: hsl(var(--background));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    padding: 1rem;
    height: 600px;
    overflow-y: auto;
}

.chat-panel {
    background: hsl(var(--secondary));
}

.response-panel {
    background: hsl(var(--background));
}

.citations-panel {
    background: hsl(var(--muted));
}

.message-user {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    padding: 0.75rem;
    border-radius: var(--radius);
    margin: 0.5rem 0;
    margin-left: 2rem;
}

.message-assistant {
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
    margin-bottom: 0.25rem;
}

.citation-content {
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
    line-height: 1.4;
}

.header-title {
    color: hsl(var(--primary));
    font-weight: 600;
    font-size: 1.25rem;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid hsl(var(--border));
}

.input-area {
    position: sticky;
    bottom: 0;
    background: hsl(var(--background));
    padding: 1rem;
    border-top: 1px solid hsl(var(--border));
    margin: -1rem;
    margin-top: 1rem;
}

.stTextInput > div > div > input {
    border: 1px solid hsl(var(--input));
    border-radius: var(--radius);
    background: hsl(var(--background));
    color: hsl(var(--foreground));
}

.stTextInput > div > div > input:focus {
    border-color: hsl(var(--ring));
    box-shadow: 0 0 0 2px hsl(var(--ring)/20%);
}

.stButton > button {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border: none;
    border-radius: var(--radius);
    padding: 0.5rem 1rem;
    font-weight: 500;
    transition: all 0.2s;
}

.stButton > button:hover {
    background: hsl(var(--primary)/90%);
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
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'vector_store' not in st.session_state:
    st.session_state.vector_store = LocalVectorStore()

if 'dual_agent' not in st.session_state:
    st.session_state.dual_agent = LocalDualAgentOrchestrator()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'current_response' not in st.session_state:
    st.session_state.current_response = None

if 'current_citations' not in st.session_state:
    st.session_state.current_citations = []

# Main header
st.markdown("# NSW Revenue AI Assistant")
st.markdown("Professional legal assistance for NSW Revenue matters")

# Create 3-column layout
col1, col2, col3 = st.columns([1, 2, 1])

# LEFT PANEL - Chat History and Input
with col1:
    st.markdown('<div class="header-title">Chat</div>', unsafe_allow_html=True)

    # Chat history container
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="panel chat-panel">', unsafe_allow_html=True)

        # Display chat history
        for message in st.session_state.chat_history:
            if message['role'] == 'user':
                st.markdown(f'<div class="message-user">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="message-assistant">{message["content"][:100]}...</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Input area
    st.markdown('<div class="input-area">', unsafe_allow_html=True)

    # Query input
    query = st.text_input(
        "Ask about NSW Revenue legislation:",
        placeholder="e.g., What is the payroll tax rate?",
        key="query_input"
    )

    # Submit button
    if st.button("Send", type="primary", use_container_width=True):
        if query.strip():
            # Add user message to history
            st.session_state.chat_history.append({
                'role': 'user',
                'content': query
            })

            # Process query with local vector store and dual agents
            try:
                # Search relevant documents
                relevant_docs = st.session_state.vector_store.search(query, k=5, threshold=0.3)

                # Generate response using dual agent system
                response = st.session_state.dual_agent.process_query(query, enable_approval=True)

                # Store current response and citations
                st.session_state.current_response = response
                st.session_state.current_citations = relevant_docs

                # Add assistant response to history
                assistant_message = response.final_response.content if hasattr(response, 'final_response') else str(response)
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': assistant_message
                })

            except Exception as e:
                st.error(f"Error processing query: {str(e)}")
                # Add fallback response
                st.session_state.current_response = "I apologize, but I'm currently unable to process your query. Please try again."
                st.session_state.current_citations = []

            # Clear input and rerun to update display
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# CENTER PANEL - AI Response
with col2:
    st.markdown('<div class="header-title">AI Response</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel response-panel">', unsafe_allow_html=True)

    if st.session_state.current_response:
        # Display status badge
        if hasattr(st.session_state.current_response, 'approval_decision'):
            if st.session_state.current_response.approval_decision.is_approved:
                st.markdown('<span class="status-badge status-success">Approved Response</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-badge status-info">Pending Review</span>', unsafe_allow_html=True)

        # Display response content
        if hasattr(st.session_state.current_response, 'final_response'):
            response_content = st.session_state.current_response.final_response.content
            st.markdown(response_content)

            # Display confidence score if available
            if hasattr(st.session_state.current_response.final_response, 'confidence_score'):
                confidence = st.session_state.current_response.final_response.confidence_score
                st.markdown(f"**Confidence Score:** {confidence:.2f}")
        else:
            st.markdown(str(st.session_state.current_response))
    else:
        st.markdown("Welcome to the NSW Revenue AI Assistant. Ask a question to get started.")

        # Show sample queries
        st.markdown("**Sample Questions:**")
        sample_queries = [
            "What is the current payroll tax rate in NSW?",
            "How does the principal place of residence exemption work for land tax?",
            "What are the stamp duty rates for property purchases?",
            "What is the threshold for payroll tax?",
            "How do I apply for first home buyer concessions?"
        ]

        for sample in sample_queries:
            if st.button(sample, key=f"sample_{hash(sample)}", use_container_width=True):
                st.session_state.query_input = sample
                st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# RIGHT PANEL - Citations and References
with col3:
    st.markdown('<div class="header-title">Citations & References</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel citations-panel">', unsafe_allow_html=True)

    if st.session_state.current_citations:
        for i, citation in enumerate(st.session_state.current_citations, 1):
            st.markdown(f'''
            <div class="citation-item">
                <div class="citation-title">{i}. {citation['act_name'].replace('_', ' ').title()}</div>
                <div class="citation-content">
                    <strong>Section:</strong> {citation.get('section_number', 'N/A')}<br>
                    <strong>Similarity:</strong> {citation.get('similarity_score', 0):.2f}<br>
                    <strong>Content:</strong> {citation['content'][:150]}...
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.markdown("Relevant legal citations and references will appear here when you ask a question.")

        # Show available acts
        try:
            available_acts = st.session_state.vector_store.list_available_acts()
            if available_acts:
                st.markdown("**Available NSW Revenue Acts:**")
                for act in available_acts:
                    act_display = act.replace('_', ' ').title()
                    st.markdown(f"• {act_display}")
        except Exception:
            pass

    st.markdown('</div>', unsafe_allow_html=True)

# Footer with system status
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    # Check vector store status
    try:
        acts_count = len(st.session_state.vector_store.list_available_acts())
        st.success(f"Vector Store: {acts_count} Acts Loaded")
    except Exception:
        st.warning("Vector Store: Initializing...")

with col2:
    # Check dual agent status
    st.info("Dual Agent System: Active")

with col3:
    # Cost optimization status
    st.info("Cost Optimized: GPT-3.5 Turbo")