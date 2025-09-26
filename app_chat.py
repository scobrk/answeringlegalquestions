"""
NSW Revenue AI Assistant - Modern Chat Interface
Clean, functional chat interface with source timeline and references
"""

import streamlit as st
import os
import sys
import time
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
/* Global styles */
.main {
    padding: 0;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: none;
}

/* Chat container */
.chat-container {
    display: flex;
    flex-direction: column;
    height: 70vh;
    overflow-y: auto;
    padding: 1rem;
    background: #f8f9fa;
    border-radius: 12px;
    border: 1px solid #e9ecef;
    margin-bottom: 1rem;
}

/* Message bubbles */
.message {
    margin: 0.5rem 0;
    display: flex;
    align-items: flex-start;
    gap: 0.75rem;
}

.message.user {
    flex-direction: row-reverse;
}

.message-bubble {
    max-width: 70%;
    padding: 1rem 1.25rem;
    border-radius: 18px;
    font-size: 0.95rem;
    line-height: 1.4;
    word-wrap: break-word;
}

.message.user .message-bubble {
    background: #007bff;
    color: white;
    border-bottom-right-radius: 6px;
}

.message.assistant .message-bubble {
    background: white;
    color: #333;
    border: 1px solid #e9ecef;
    border-bottom-left-radius: 6px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* Avatar circles */
.avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 0.8rem;
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

/* Confidence badges */
.confidence-badge {
    display: inline-block;
    padding: 0.2rem 0.5rem;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
    margin-left: 0.5rem;
}

.confidence-high {
    background: #d4edda;
    color: #155724;
}

.confidence-medium {
    background: #fff3cd;
    color: #856404;
}

.confidence-low {
    background: #f8d7da;
    color: #721c24;
}

/* Header */
.chat-header {
    background: linear-gradient(90deg, #007bff, #6610f2);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
    text-align: center;
}

.chat-header h1 {
    margin: 0;
    font-size: 1.5rem;
    font-weight: 600;
}

.chat-header p {
    margin: 0.5rem 0 0 0;
    opacity: 0.9;
    font-size: 0.9rem;
}
    --error-color: #ef4444;
    --sidebar-bg: #f8fafc;
    --message-bg-user: #0066cc;
    --message-bg-assistant: #f1f5f9;
    --shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
}

/* Hide Streamlit default elements */
#MainMenu {visibility: hidden;}
.stDeployButton {display: none;}
footer {visibility: hidden;}
.stApp > header {visibility: hidden;}

/* Main container */
.main .block-container {
    max-width: 100%;
    padding: 0;
    margin: 0;
}

/* Chat container */
.chat-container {
    height: calc(100vh - 120px);
    display: flex;
    flex-direction: column;
    background: var(--background-color);
}

/* Messages area */
.messages-container {
    flex: 1;
    overflow-y: auto;
    padding: 2rem 1rem;
    background: var(--background-color);
}

/* Individual message styles */
.message {
    max-width: 800px;
    margin: 0 auto 1.5rem auto;
    padding: 0;
}

.message-user {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 1rem;
}

.message-user .message-content {
    background: var(--message-bg-user);
    color: white;
    padding: 0.75rem 1rem;
    border-radius: 18px 18px 4px 18px;
    max-width: 70%;
    word-wrap: break-word;
    box-shadow: var(--shadow);
}

.message-assistant {
    display: flex;
    justify-content: flex-start;
    margin-bottom: 1rem;
}

.message-assistant .message-content {
    background: var(--message-bg-assistant);
    color: var(--text-color);
    padding: 1rem 1.25rem;
    border-radius: 18px 18px 18px 4px;
    max-width: 85%;
    word-wrap: break-word;
    box-shadow: var(--shadow);
    border: 1px solid var(--border-color);
}

/* Assistant message styling */
.assistant-header {
    display: flex;
    align-items: center;
    margin-bottom: 0.5rem;
    gap: 0.5rem;
}

.confidence-badge {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-weight: 500;
}

.confidence-high {
    background: rgba(34, 197, 94, 0.1);
    color: #15803d;
    border: 1px solid rgba(34, 197, 94, 0.2);
}

.confidence-medium {
    background: rgba(245, 158, 11, 0.1);
    color: #d97706;
    border: 1px solid rgba(245, 158, 11, 0.2);
}

.confidence-low {
    background: rgba(239, 68, 68, 0.1);
    color: #dc2626;
    border: 1px solid rgba(239, 68, 68, 0.2);
}

.approval-badge {
    font-size: 0.75rem;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-weight: 500;
}

.approved {
    background: rgba(34, 197, 94, 0.1);
    color: #15803d;
    border: 1px solid rgba(34, 197, 94, 0.2);
}

.pending {
    background: rgba(245, 158, 11, 0.1);
    color: #d97706;
    border: 1px solid rgba(245, 158, 11, 0.2);
}

/* Citations in messages */
.citation-inline {
    background: rgba(59, 130, 246, 0.1);
    color: #1d4ed8;
    padding: 0.125rem 0.25rem;
    border-radius: 4px;
    font-size: 0.875rem;
    cursor: pointer;
    text-decoration: none;
    border: 1px solid rgba(59, 130, 246, 0.2);
}

.citation-inline:hover {
    background: rgba(59, 130, 246, 0.2);
}

/* Input area */
.input-container {
    position: sticky;
    bottom: 0;
    background: var(--background-color);
    border-top: 1px solid var(--border-color);
    padding: 1rem;
}

.input-wrapper {
    max-width: 800px;
    margin: 0 auto;
    position: relative;
}

/* Sidebar styling */
.sidebar .sidebar-content {
    background: var(--sidebar-bg);
    padding: 1rem;
}

.source-timeline {
    margin-top: 1rem;
}

.timeline-item {
    background: var(--background-color);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow);
}

.timeline-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.5rem;
}

.timeline-source {
    font-weight: 600;
    color: var(--primary-color);
    font-size: 0.875rem;
}

.timeline-score {
    font-size: 0.75rem;
    padding: 0.125rem 0.375rem;
    background: rgba(59, 130, 246, 0.1);
    color: #1d4ed8;
    border-radius: 12px;
}

.timeline-content {
    font-size: 0.875rem;
    color: #6b7280;
    line-height: 1.4;
}

/* Loading states */
.loading-message {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 1rem 1.25rem;
    background: var(--message-bg-assistant);
    border-radius: 18px 18px 18px 4px;
    max-width: 85%;
    box-shadow: var(--shadow);
    border: 1px solid var(--border-color);
    margin-bottom: 1rem;
}

.loading-dots {
    display: flex;
    gap: 4px;
}

.loading-dot {
    width: 8px;
    height: 8px;
    background: #9ca3af;
    border-radius: 50%;
    animation: loading 1.4s ease-in-out infinite both;
}

.loading-dot:nth-child(1) { animation-delay: -0.32s; }
.loading-dot:nth-child(2) { animation-delay: -0.16s; }
.loading-dot:nth-child(3) { animation-delay: 0s; }

@keyframes loading {
    0%, 80%, 100% {
        transform: scale(0);
    }
    40% {
        transform: scale(1);
    }
}

/* Welcome screen */
.welcome-container {
    text-align: center;
    padding: 3rem 2rem;
    max-width: 600px;
    margin: 0 auto;
}

.welcome-title {
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-color);
    margin-bottom: 0.5rem;
}

.welcome-subtitle {
    font-size: 1.125rem;
    color: #6b7280;
    margin-bottom: 2rem;
}

.example-questions {
    display: grid;
    gap: 0.75rem;
    margin-top: 2rem;
}

.example-question {
    background: var(--secondary-color);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
}

.example-question:hover {
    background: #e2e8f0;
    transform: translateY(-1px);
    box-shadow: var(--shadow);
}

/* Responsive design */
@media (max-width: 768px) {
    .message-content {
        max-width: 95% !important;
    }

    .welcome-container {
        padding: 2rem 1rem;
    }

    .welcome-title {
        font-size: 1.5rem;
    }
}

/* Custom Streamlit component overrides */
.stTextInput > div > div > input {
    border: 1px solid var(--border-color);
    border-radius: 24px;
    padding: 0.75rem 1rem;
    font-size: 1rem;
    background: var(--background-color);
    color: var(--text-color);
}

.stTextInput > div > div > input:focus {
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
}

.stButton > button {
    background: var(--primary-color);
    color: white;
    border: none;
    border-radius: 20px;
    padding: 0.5rem 1.5rem;
    font-weight: 500;
    transition: all 0.2s;
}

.stButton > button:hover {
    background: #0052a3;
    transform: translateY(-1px);
}

.stSpinner > div {
    border-color: var(--primary-color) transparent transparent transparent;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize session state variables"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'orchestrator' not in st.session_state:
        st.session_state.orchestrator = LocalDualAgentOrchestrator()

    if 'context_layer' not in st.session_state:
        st.session_state.context_layer = DynamicContextLayer()

    if 'source_timeline' not in st.session_state:
        st.session_state.source_timeline = []

    if 'processing' not in st.session_state:
        st.session_state.processing = False

def add_message(role: str, content: str, metadata: Optional[Dict] = None):
    """Add a message to the chat history"""
    message = {
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'metadata': metadata or {}
    }
    st.session_state.messages.append(message)

def format_confidence_badge(confidence: float) -> str:
    """Format confidence score as a colored badge"""
    if confidence >= 0.8:
        badge_class = "confidence-high"
        label = "High Confidence"
    elif confidence >= 0.6:
        badge_class = "confidence-medium"
        label = "Medium Confidence"
    else:
        badge_class = "confidence-low"
        label = "Low Confidence"

    return f'<span class="confidence-badge {badge_class}">{label} ({confidence:.1%})</span>'

def format_approval_badge(is_approved: bool) -> str:
    """Format approval status as a colored badge"""
    if is_approved:
        return '<span class="approval-badge approved">✓ Verified</span>'
    else:
        return '<span class="approval-badge pending">⚠ Pending Review</span>'

def render_message(message: Dict):
    """Render a single message in the chat"""
    if message['role'] == 'user':
        st.markdown(f'''
        <div class="message-user">
            <div class="message-content">{message['content']}</div>
        </div>
        ''', unsafe_allow_html=True)

    elif message['role'] == 'assistant':
        metadata = message.get('metadata', {})

        # Prepare header with badges
        header_html = '<div class="assistant-header">'

        if 'confidence' in metadata:
            header_html += format_confidence_badge(metadata['confidence'])

        if 'approved' in metadata:
            header_html += format_approval_badge(metadata['approved'])

        header_html += '</div>'

        # Format content with inline citations
        content = message['content']
        if 'citations' in metadata and metadata['citations']:
            for i, citation in enumerate(metadata['citations'], 1):
                # Add citation markers in content
                citation_marker = f'<span class="citation-inline" title="{citation[:100]}...">[{i}]</span>'
                # This is a simple implementation - in a real app you'd want more sophisticated citation placement

        st.markdown(f'''
        <div class="message-assistant">
            <div class="message-content">
                {header_html}
                {content}
            </div>
        </div>
        ''', unsafe_allow_html=True)

def render_sidebar():
    """Render the sidebar with source timeline and settings"""
    with st.sidebar:
        st.markdown("## ⚖️ NSW Revenue AI")
        st.markdown("Expert guidance on NSW taxation and revenue matters")

        # System status
        st.markdown("### 📊 System Status")
        try:
            health = st.session_state.orchestrator.health_check()
            status = health.get('orchestrator_status', 'unknown')

            if status == 'healthy':
                st.success("🟢 System Online")
            elif status == 'degraded':
                st.warning("🟡 Limited Functionality")
            else:
                st.error("🔴 System Offline")
        except Exception:
            st.error("🔴 System Check Failed")

        # Source timeline
        st.markdown("### 📚 Source Timeline")

        if st.session_state.source_timeline:
            for item in st.session_state.source_timeline[-5:]:  # Show last 5 sources
                st.markdown(f'''
                <div class="timeline-item">
                    <div class="timeline-header">
                        <span class="timeline-source">{item.get('title', 'Unknown Source')}</span>
                        <span class="timeline-score">{item.get('relevance_score', 0):.2f}</span>
                    </div>
                    <div class="timeline-content">{item.get('content', '')[:100]}...</div>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.markdown("*Source references will appear here as you ask questions*")

        # Settings
        st.markdown("### ⚙️ Settings")

        enable_approval = st.checkbox(
            "Enhanced Validation",
            value=True,
            help="Use dual-agent validation for higher accuracy"
        )

        show_citations = st.checkbox(
            "Show Citations",
            value=True,
            help="Display source citations in responses"
        )

        st.session_state.settings = {
            'enable_approval': enable_approval,
            'show_citations': show_citations
        }

        # Example questions
        st.markdown("### 💡 Example Questions")

        examples = [
            "What is the current payroll tax rate in NSW?",
            "How do I calculate stamp duty on a $800k property?",
            "What are the land tax exemptions available?",
            "How do I appeal a Revenue NSW penalty?",
            "Am I eligible for first home buyer concessions?"
        ]

        for example in examples:
            if st.button(example, key=f"example_{hash(example)}", use_container_width=True):
                st.session_state.pending_query = example
                st.rerun()

def render_welcome_screen():
    """Render the welcome screen when no messages exist"""
    st.markdown('''
    <div class="welcome-container">
        <div class="welcome-title">NSW Revenue AI Assistant</div>
        <div class="welcome-subtitle">Get expert guidance on NSW taxation and revenue matters</div>

        <div style="margin: 2rem 0;">
            <p>I can help you with:</p>
            <ul style="text-align: left; display: inline-block;">
                <li>Payroll tax calculations and thresholds</li>
                <li>Land tax exemptions and rates</li>
                <li>Stamp duty for property purchases</li>
                <li>First home buyer concessions</li>
                <li>Revenue penalties and appeals</li>
            </ul>
        </div>

        <p><strong>Ask me a question to get started!</strong></p>
    </div>
    ''', unsafe_allow_html=True)

def process_query(query: str):
    """Process a user query through the AI system"""
    if not query.strip():
        return

    # Add user message
    add_message('user', query)

    # Set processing state
    st.session_state.processing = True

    try:
        # Get settings
        settings = getattr(st.session_state, 'settings', {
            'enable_approval': True,
            'show_citations': True
        })

        # Process through dual agent system
        response = st.session_state.orchestrator.process_query(
            query=query,
            enable_approval=settings['enable_approval'],
            include_metadata=True
        )

        # Extract response data
        if hasattr(response, 'final_response'):
            content = response.final_response.content
            confidence = getattr(response.final_response, 'confidence_score', 0.0)
            citations = getattr(response.final_response, 'citations', [])
            source_docs = getattr(response.final_response, 'source_documents', [])
            approved = getattr(response.approval_decision, 'is_approved', False) if hasattr(response, 'approval_decision') else True
        else:
            content = str(response)
            confidence = 0.0
            citations = []
            source_docs = []
            approved = False

        # Update source timeline
        for doc in source_docs:
            if doc not in st.session_state.source_timeline:
                st.session_state.source_timeline.append(doc)

        # Prepare metadata
        metadata = {
            'confidence': confidence,
            'approved': approved,
            'citations': citations if settings['show_citations'] else [],
            'processing_time': getattr(response, 'total_processing_time', 0.0)
        }

        # Add assistant response
        add_message('assistant', content, metadata)

    except Exception as e:
        # Add error message
        error_content = f"I apologize, but I encountered an error processing your question: {str(e)}"
        add_message('assistant', error_content, {'confidence': 0.0, 'approved': False})

    finally:
        # Clear processing state
        st.session_state.processing = False

def render_loading_message():
    """Render a loading message while processing"""
    st.markdown('''
    <div class="message-assistant">
        <div class="loading-message">
            <span>Thinking</span>
            <div class="loading-dots">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Main chat container
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # Messages area
    st.markdown('<div class="messages-container">', unsafe_allow_html=True)

    if not st.session_state.messages:
        render_welcome_screen()
    else:
        # Render all messages
        for message in st.session_state.messages:
            render_message(message)

        # Show loading if processing
        if st.session_state.processing:
            render_loading_message()

    st.markdown('</div>', unsafe_allow_html=True)

    # Input area
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)

    # Check for pending query from sidebar examples
    if hasattr(st.session_state, 'pending_query'):
        query = st.session_state.pending_query
        del st.session_state.pending_query
        process_query(query)
        st.rerun()

    # Query input form
    with st.form(key="query_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])

        with col1:
            query = st.text_input(
                "Ask about NSW Revenue legislation...",
                placeholder="e.g., What is the payroll tax rate for wages over $1.2 million?",
                label_visibility="collapsed",
                disabled=st.session_state.processing
            )

        with col2:
            submit = st.form_submit_button(
                "Send",
                type="primary",
                disabled=st.session_state.processing or not query.strip(),
                use_container_width=True
            )

    # Process query if submitted
    if submit and query.strip() and not st.session_state.processing:
        process_query(query)
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()