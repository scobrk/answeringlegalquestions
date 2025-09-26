"""
NSW Revenue AI Assistant - Modern Chat Interface
Clean, functional chat interface with source timeline and references
"""

import streamlit as st
import os
import sys
import time
import re
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import local modules
from data.dynamic_context_layer import DynamicContextLayer
from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator
from agents.interpretation_agent import InterpretationAgent

def format_response_content(content: str) -> str:
    """Format response content for proper HTML display with line breaks and lists"""
    if not content:
        return ""

    # Convert numbered lists
    content = re.sub(r'^(\d+\.)\s*(\*\*[^*]+\*\*:?)\s*(.+)$', r'<div class="list-item"><span class="list-number">\1</span><strong>\2</strong> \3</div>', content, flags=re.MULTILINE)

    # Convert bullet points
    content = re.sub(r'^-\s*(\*\*[^*]+\*\*:?)\s*(.+)$', r'<div class="list-item"><span class="bullet">•</span><strong>\1</strong> \2</div>', content, flags=re.MULTILINE)

    # Convert bold text
    content = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', content)

    # Convert line breaks to <br> tags, but avoid double breaks for list items
    lines = content.split('\n')
    formatted_lines = []

    for line in lines:
        line = line.strip()
        if line:
            if '<div class="list-item">' in line:
                formatted_lines.append(line)
            else:
                formatted_lines.append(line + '<br>')
        else:
            formatted_lines.append('<br>')

    return ''.join(formatted_lines)

# Page configuration
st.set_page_config(
    page_title="NSW Revenue AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern chat CSS
st.markdown("""
<style>
/* Chat container */
.chat-container {
    height: 500px;
    overflow-y: auto;
    padding: 1rem;
    background: #f8f9fa !important;
    border-radius: 8px;
    border: 2px solid #dee2e6;
    margin-bottom: 1rem;
    min-height: 500px;
    display: block !important;
    position: relative;
}

/* List formatting */
.list-item {
    margin: 0.5rem 0;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    line-height: 1.5;
}

.list-number {
    font-weight: bold;
    color: #007bff;
    min-width: 1.5rem;
    flex-shrink: 0;
}

.bullet {
    color: #007bff;
    font-weight: bold;
    min-width: 1rem;
    flex-shrink: 0;
}

/* Message bubbles */
.message {
    margin: 0.5rem 0;
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
}

.message.user {
    flex-direction: row-reverse;
}

.message-bubble {
    max-width: 70%;
    padding: 0.75rem 1rem;
    border-radius: 12px;
    font-size: 0.9rem;
    line-height: 1.4;
}

.message.user .message-bubble {
    background: #007bff !important;
    color: white !important;
    border: 1px solid #0056b3;
}

.message.assistant .message-bubble {
    background: white !important;
    color: #333 !important;
    border: 1px solid #dee2e6;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Avatar */
.avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 0.7rem;
    flex-shrink: 0;
}

.avatar.user {
    background: #007bff;
    color: white;
}

.avatar.assistant {
    background: #6c757d;
    color: white;
}

/* Confidence badge */
.confidence-badge {
    display: inline-block;
    padding: 0.15rem 0.4rem;
    border-radius: 8px;
    font-size: 0.65rem;
    font-weight: 600;
    margin-left: 0.5rem;
}

.confidence-high { background: #d4edda; color: #155724; }
.confidence-medium { background: #fff3cd; color: #856404; }
.confidence-low { background: #f8d7da; color: #721c24; }

/* Source cards */
.source-card {
    background: white;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 0.6rem;
    margin: 0.4rem 0;
    font-size: 0.8rem;
}

.source-header {
    font-weight: 600;
    margin-bottom: 0.3rem;
    color: #495057;
}

.relevance-score {
    padding: 0.1rem 0.3rem;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 600;
}

.score-high { background: #d4edda; color: #155724; }
.score-medium { background: #fff3cd; color: #856404; }
.score-low { background: #f8d7da; color: #721c24; }

/* Interpretation panel */
.interpretation-panel {
    background: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 0.8rem;
    margin: 0.5rem 0;
    font-size: 0.85rem;
}

.interpretation-header {
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: #495057;
}

.gap-warning {
    background: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
    border-radius: 4px;
    padding: 0.4rem;
    margin: 0.3rem 0;
    font-size: 0.8rem;
}

.completeness-score {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 600;
    margin: 0.2rem 0;
}

.completeness-high { background: #d4edda; color: #155724; }
.completeness-medium { background: #fff3cd; color: #856404; }
.completeness-low { background: #f8d7da; color: #721c24; }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'context_layer' not in st.session_state:
    st.session_state.context_layer = DynamicContextLayer()

if 'dual_agent' not in st.session_state:
    st.session_state.dual_agent = LocalDualAgentOrchestrator()

if 'interpretation_agent' not in st.session_state:
    st.session_state.interpretation_agent = InterpretationAgent()

if 'messages' not in st.session_state:
    st.session_state.messages = []

if 'current_sources' not in st.session_state:
    st.session_state.current_sources = []

if 'current_interpretation' not in st.session_state:
    st.session_state.current_interpretation = None

if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

# Header
st.markdown("# NSW Revenue AI Assistant")
st.markdown("Ask questions about NSW taxation and revenue legislation")

# Layout: Sidebar for sources, main area for chat
with st.sidebar:
    st.markdown("## Source Analysis")

    if st.session_state.current_interpretation:
        interp = st.session_state.current_interpretation

        # Completeness score
        completeness_class = ("completeness-high" if interp.completeness_score > 0.7
                            else "completeness-medium" if interp.completeness_score > 0.4
                            else "completeness-low")

        st.markdown(f'''
        <div class="interpretation-panel">
            <div class="interpretation-header">Source Quality Assessment</div>
            <div>Completeness: <span class="completeness-score {completeness_class}">{interp.completeness_score:.2f}</span></div>
            <div>Confidence: <span class="completeness-score {completeness_class}">{interp.confidence:.2f}</span></div>
        </div>
        ''', unsafe_allow_html=True)

        # Missing information warnings
        if interp.missing_information:
            st.markdown('<div class="interpretation-header">⚠️ Missing Information</div>', unsafe_allow_html=True)
            for missing in interp.missing_information:
                st.markdown(f'<div class="gap-warning">• {missing}</div>', unsafe_allow_html=True)

        # Source gaps
        if interp.source_gaps:
            st.markdown('<div class="interpretation-header">📍 Source Gaps</div>', unsafe_allow_html=True)
            for gap in interp.source_gaps:
                st.markdown(f'<div class="gap-warning">• {gap}</div>', unsafe_allow_html=True)

    st.markdown("## Source Timeline")

    if st.session_state.current_sources:
        st.markdown(f"**{len(st.session_state.current_sources)} sources found**")

        for i, source in enumerate(st.session_state.current_sources, 1):
            score = source.relevance_score
            score_class = "score-high" if score > 0.3 else "score-medium" if score > 0.1 else "score-low"

            st.markdown(f'''
            <div class="source-card">
                <div class="source-header">
                    {i}. {source.title}
                    <span class="relevance-score {score_class}">{score:.3f}</span>
                </div>
                <div style="font-size: 0.75rem; color: #6c757d;">
                    Source: {source.source.replace('_', ' ').title()}<br>
                    {source.content[:80]}...
                </div>
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("Sources will appear here when you ask questions")

    st.markdown("---")
    st.markdown("### Settings")
    enable_approval = st.checkbox("Enhanced Validation", value=True)
    show_sources = st.checkbox("Show Sources", value=True)
    enable_interpretation = st.checkbox("Source Analysis", value=True)

# Main chat area
col1, col2 = st.columns([3, 1])

with col1:
    # Chat display container
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        # Display messages with enhanced styling
        if st.session_state.messages:
            for i, message in enumerate(st.session_state.messages):
                if message['role'] == 'user':
                    st.markdown(f'''
                    <div class="message user">
                        <div class="avatar user">U</div>
                        <div class="message-bubble">{message['content']}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    confidence = message.get('confidence', 0)
                    conf_class = "confidence-high" if confidence > 0.7 else "confidence-medium" if confidence > 0.4 else "confidence-low"
                    conf_text = "High" if confidence > 0.7 else "Medium" if confidence > 0.4 else "Low"

                    badge = f'<span class="confidence-badge {conf_class}">{conf_text}</span>' if confidence > 0 else ''

                    formatted_content = format_response_content(message['content'][:2000])
                    st.markdown(f'''
                    <div class="message assistant">
                        <div class="avatar assistant">AI</div>
                        <div class="message-bubble">
                            {formatted_content}
                            {badge}
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align: center; color: #6c757d; padding: 2rem;">No messages yet. Ask a question to get started!</div>', unsafe_allow_html=True)

        if st.session_state.is_processing:
            st.markdown('''
            <div class="message assistant">
                <div class="avatar assistant">AI</div>
                <div class="message-bubble" style="color: #6c757d;">
                    <em>Thinking...</em>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Input form
    with st.form("chat_form", clear_on_submit=True):
        col_input, col_send = st.columns([4, 1])

        with col_input:
            user_input = st.text_input(
                "Message",
                placeholder="Ask about NSW Revenue legislation...",
                label_visibility="collapsed",
                disabled=st.session_state.is_processing
            )

        with col_send:
            send_clicked = st.form_submit_button(
                "Send",
                use_container_width=True,
                disabled=st.session_state.is_processing
            )

with col2:
    st.markdown("### Chat Stats")
    st.metric("Messages", len(st.session_state.messages))

    if st.session_state.current_sources:
        avg_rel = sum(s.relevance_score for s in st.session_state.current_sources) / len(st.session_state.current_sources)
        st.metric("Avg Relevance", f"{avg_rel:.3f}")

    if st.button("Clear Chat", type="secondary", use_container_width=True):
        st.session_state.messages = []
        st.session_state.current_sources = []
        st.rerun()

# Process message
if send_clicked and user_input.strip() and not st.session_state.is_processing:
    # Add user message
    st.session_state.messages.append({
        'role': 'user',
        'content': user_input,
        'timestamp': time.time()
    })

    # Set processing flag
    st.session_state.is_processing = True
    st.rerun()

# Handle AI response generation
if st.session_state.is_processing:
    if st.session_state.messages and st.session_state.messages[-1]['role'] == 'user':
        query = st.session_state.messages[-1]['content']

        try:
            # Get context
            with st.spinner("Retrieving context..."):
                context_docs = st.session_state.context_layer.get_relevant_context(query, max_docs=5)
                st.session_state.current_sources = context_docs

            # Interpret sources if enabled
            if enable_interpretation and context_docs:
                with st.spinner("Analyzing sources..."):
                    interpretation = st.session_state.interpretation_agent.interpret_sources(query, context_docs)
                    st.session_state.current_interpretation = interpretation
            else:
                st.session_state.current_interpretation = None

            # Generate response
            with st.spinner("Generating response..."):
                response = st.session_state.dual_agent.process_query(query, enable_approval=enable_approval)

            # Format response
            if hasattr(response, 'final_response'):
                content = response.final_response.content
                confidence = getattr(response.final_response, 'confidence_score', 0.0)

                # Add interpretation warnings if available
                if st.session_state.current_interpretation:
                    interp = st.session_state.current_interpretation

                    if interp.missing_information or interp.source_gaps:
                        content += "\n\n**⚠️ Source Analysis Warnings:**"
                        if interp.missing_information:
                            content += f"\n• Missing information: {', '.join(interp.missing_information[:2])}"
                            if len(interp.missing_information) > 2:
                                content += f" (+{len(interp.missing_information)-2} more)"
                        if interp.source_gaps:
                            content += f"\n• Source gaps: {', '.join(interp.source_gaps[:2])}"
                            if len(interp.source_gaps) > 2:
                                content += f" (+{len(interp.source_gaps)-2} more)"

                    if interp.completeness_score < 0.7:
                        content += f"\n\n**Note:** Source completeness is {interp.completeness_score:.1%}. Consider seeking additional sources for comprehensive guidance."

                if show_sources and st.session_state.current_sources:
                    content += f"\n\n**Sources:** {len(st.session_state.current_sources)} documents"
            else:
                content = str(response)
                confidence = 0.0

            # Add AI message
            st.session_state.messages.append({
                'role': 'assistant',
                'content': content,
                'confidence': confidence,
                'timestamp': time.time()
            })

        except Exception as e:
            st.session_state.messages.append({
                'role': 'assistant',
                'content': f"Error: {str(e)}",
                'confidence': 0.0,
                'timestamp': time.time()
            })

        finally:
            st.session_state.is_processing = False
            st.rerun()

# Footer
st.markdown("---")
st.markdown("**Status:** Processing..." if st.session_state.is_processing else "**Status:** Ready")