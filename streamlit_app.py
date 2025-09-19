"""
NSW Revenue AI Assistant - Streamlit Web Interface
Frontend Implementation (KAN-6)
"""

import streamlit as st
import os
import time
import json
from datetime import datetime
from typing import Dict, List, Optional
import logging

# Import our dual-agent system
import sys
sys.path.append('./agents')

try:
    from agents.dual_agent_orchestrator import DualAgentOrchestrator, DualAgentResponse
except ImportError:
    st.error("⚠️ Backend agents not available. Please ensure the agents directory is properly configured.")
    st.stop()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="NSW Revenue AI Assistant",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f4e79;
    text-align: center;
    margin-bottom: 1rem;
}

.sub-header {
    font-size: 1.2rem;
    color: #666;
    text-align: center;
    margin-bottom: 2rem;
}

.query-box {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f4e79;
    margin: 1rem 0;
}

.response-box {
    background-color: #ffffff;
    padding: 1.5rem;
    border-radius: 0.5rem;
    border: 1px solid #e0e0e0;
    margin: 1rem 0;
}

.validation-approved {
    background-color: #d4edda;
    color: #155724;
    padding: 0.5rem;
    border-radius: 0.25rem;
    margin: 0.5rem 0;
}

.validation-flagged {
    background-color: #f8d7da;
    color: #721c24;
    padding: 0.5rem;
    border-radius: 0.25rem;
    margin: 0.5rem 0;
}

.confidence-high { color: #28a745; }
.confidence-medium { color: #ffc107; }
.confidence-low { color: #dc3545; }

.metadata-section {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-top: 1rem;
    font-size: 0.9rem;
}
</style>
""", unsafe_allow_html=True)


class NSWRevenueAssistantUI:
    """Main UI class for the NSW Revenue AI Assistant"""

    def __init__(self):
        self.orchestrator = None
        self._initialize_session_state()
        self._initialize_orchestrator()

    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []

        if 'current_response' not in st.session_state:
            st.session_state.current_response = None

        if 'ui_settings' not in st.session_state:
            st.session_state.ui_settings = {
                'enable_approval': True,
                'show_metadata': False,
                'show_validation_details': True,
                'auto_scroll': True
            }

    def _initialize_orchestrator(self):
        """Initialize the dual-agent orchestrator"""
        try:
            # Get API keys from environment or Streamlit secrets
            openai_key = os.getenv('OPENAI_API_KEY') or st.secrets.get('OPENAI_API_KEY')
            supabase_url = os.getenv('SUPABASE_URL') or st.secrets.get('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY') or st.secrets.get('SUPABASE_KEY')

            if not openai_key:
                st.error("⚠️ OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.")
                return

            self.orchestrator = DualAgentOrchestrator(
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                openai_api_key=openai_key
            )

            # Configure orchestrator based on UI settings
            self.orchestrator.configure_orchestration(
                enable_approval=st.session_state.ui_settings['enable_approval'],
                max_processing_time=15.0,
                retry_on_failure=True
            )

        except Exception as e:
            st.error(f"Failed to initialize AI system: {e}")
            logger.error(f"Orchestrator initialization failed: {e}")

    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">🏛️ NSW Revenue AI Assistant</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Expert guidance on NSW taxation and revenue matters</p>', unsafe_allow_html=True)

        # System status indicator
        if self.orchestrator:
            health = self.orchestrator.health_check()
            status = health.get('orchestrator_status', 'unknown')

            if status == 'healthy':
                st.success("✅ System Online - Ready to assist with NSW Revenue queries")
            elif status == 'degraded':
                st.warning("⚠️ System Partially Available - Some features may be limited")
            else:
                st.error("❌ System Unavailable - Please try again later")
        else:
            st.error("❌ System Not Initialized")

    def render_sidebar(self):
        """Render the sidebar with settings and information"""
        with st.sidebar:
            st.header("⚙️ Settings")

            # Validation settings
            st.session_state.ui_settings['enable_approval'] = st.checkbox(
                "Enable Response Validation",
                value=st.session_state.ui_settings['enable_approval'],
                help="Use dual-agent validation for higher accuracy (slower but more reliable)"
            )

            # Display settings
            st.session_state.ui_settings['show_metadata'] = st.checkbox(
                "Show Processing Metadata",
                value=st.session_state.ui_settings['show_metadata'],
                help="Display detailed processing information and timing"
            )

            st.session_state.ui_settings['show_validation_details'] = st.checkbox(
                "Show Validation Details",
                value=st.session_state.ui_settings['show_validation_details'],
                help="Display validation scores and enhancement information"
            )

            st.divider()

            # Information section
            st.header("📋 Query Examples")
            example_queries = [
                "What is the current payroll tax rate for wages over $1.2 million?",
                "How do I calculate stamp duty on an $800,000 residential property?",
                "What are the land tax exemptions for primary residence?",
                "How do I appeal a penalty notice from Revenue NSW?",
                "Am I eligible for the first home owner grant?",
                "What is the current land tax threshold for 2024?"
            ]

            for i, example in enumerate(example_queries):
                if st.button(f"📝 {example[:40]}...", key=f"example_{i}"):
                    st.session_state.current_query = example
                    st.rerun()

            st.divider()

            # System information
            st.header("ℹ️ System Info")
            st.info("""
            **NSW Revenue AI Assistant**
            - Powered by dual-agent validation
            - Trained on NSW Revenue legislation
            - Provides citations and confidence scores
            - Validates responses for accuracy
            """)

            # Query history
            if st.session_state.query_history:
                st.header("📜 Recent Queries")
                for i, item in enumerate(reversed(st.session_state.query_history[-5:])):
                    if st.button(f"🔍 {item['query'][:30]}...", key=f"history_{i}"):
                        st.session_state.current_query = item['query']
                        st.rerun()

    def render_query_interface(self):
        """Render the main query interface"""
        st.header("💬 Ask Your NSW Revenue Question")

        # Query input
        query = st.text_area(
            "Enter your question about NSW taxation, duties, or revenue matters:",
            value=st.session_state.get('current_query', ''),
            height=100,
            placeholder="e.g., What is the payroll tax rate for wages over $1.2 million?",
            key="query_input"
        )

        # Submit button
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            submit_clicked = st.button("🚀 Get Answer", type="primary", disabled=not query.strip())

        with col2:
            if st.button("🗑️ Clear"):
                st.session_state.current_query = ""
                st.session_state.current_response = None
                st.rerun()

        # Process query
        if submit_clicked and query.strip():
            self._process_query(query.strip())

    def _process_query(self, query: str):
        """Process a user query through the dual-agent system"""
        if not self.orchestrator:
            st.error("AI system not available. Please refresh the page.")
            return

        # Update UI settings in orchestrator
        self.orchestrator.configure_orchestration(
            enable_approval=st.session_state.ui_settings['enable_approval']
        )

        # Show processing indicator
        with st.spinner("🤖 Processing your query through the dual-agent system..."):
            try:
                start_time = time.time()

                # Process query
                response = self.orchestrator.process_query(
                    query=query,
                    enable_approval=st.session_state.ui_settings['enable_approval'],
                    include_metadata=True
                )

                processing_time = time.time() - start_time

                # Store response
                st.session_state.current_response = response

                # Add to history
                history_item = {
                    'query': query,
                    'timestamp': datetime.now().isoformat(),
                    'processing_time': processing_time,
                    'approved': response.approval_decision.approved,
                    'confidence': response.final_response.final_confidence
                }
                st.session_state.query_history.append(history_item)

                # Show success message
                st.success(f"✅ Response generated in {processing_time:.2f} seconds")

            except Exception as e:
                st.error(f"❌ Error processing query: {str(e)}")
                logger.error(f"Query processing failed: {e}")

    def render_response_display(self):
        """Render the response display section"""
        if not st.session_state.current_response:
            return

        response = st.session_state.current_response

        st.header("📋 Response")

        # Query display
        st.markdown(f"""
        <div class="query-box">
            <strong>Your Question:</strong><br>
            {response.query}
        </div>
        """, unsafe_allow_html=True)

        # Validation status
        if st.session_state.ui_settings['show_validation_details']:
            approval_class = "validation-approved" if response.approval_decision.approved else "validation-flagged"
            approval_icon = "✅" if response.approval_decision.approved else "⚠️"

            st.markdown(f"""
            <div class="{approval_class}">
                {approval_icon} <strong>Validation Status:</strong> {response.final_response.validation_summary}
            </div>
            """, unsafe_allow_html=True)

        # Main answer
        st.markdown(f"""
        <div class="response-box">
            <h4>💡 Answer</h4>
            {response.final_response.final_answer}
        </div>
        """, unsafe_allow_html=True)

        # Confidence and metadata
        col1, col2, col3 = st.columns(3)

        with col1:
            confidence = response.final_response.final_confidence
            confidence_class = self._get_confidence_class(confidence)
            st.markdown(f"""
            <div style="text-align: center;">
                <h4>📊 Confidence</h4>
                <span class="{confidence_class}" style="font-size: 1.5rem; font-weight: bold;">
                    {confidence:.1%}
                </span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            approval_text = "Approved" if response.approval_decision.approved else "Flagged"
            st.markdown(f"""
            <div style="text-align: center;">
                <h4>✅ Validation</h4>
                <span style="font-size: 1.2rem; font-weight: bold;">
                    {approval_text}
                </span>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="text-align: center;">
                <h4>⏱️ Processing</h4>
                <span style="font-size: 1.2rem; font-weight: bold;">
                    {response.total_processing_time:.2f}s
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Citations
        if response.final_response.final_citations:
            st.markdown("### 📚 Legal Citations")
            for i, citation in enumerate(response.final_response.final_citations, 1):
                st.markdown(f"{i}. {citation}")

        # Enhancements applied
        if response.final_response.enhancements_applied and st.session_state.ui_settings['show_validation_details']:
            st.markdown("### 🔧 Enhancements Applied")
            for enhancement in response.final_response.enhancements_applied:
                st.markdown(f"• {enhancement}")

        # Issues (if any)
        if response.approval_decision.issues_found and st.session_state.ui_settings['show_validation_details']:
            with st.expander("⚠️ Validation Issues", expanded=False):
                for issue in response.approval_decision.issues_found:
                    st.markdown(f"• {issue}")

        # Detailed metadata
        if st.session_state.ui_settings['show_metadata']:
            with st.expander("🔍 Processing Metadata", expanded=False):
                metadata = response.to_dict()['metadata']
                st.json(metadata)

    def _get_confidence_class(self, confidence: float) -> str:
        """Get CSS class for confidence level"""
        if confidence >= 0.7:
            return "confidence-high"
        elif confidence >= 0.4:
            return "confidence-medium"
        else:
            return "confidence-low"

    def render_footer(self):
        """Render the footer"""
        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**⚠️ Disclaimer**")
            st.caption("This AI assistant provides general information only. For specific legal advice, consult a qualified professional.")

        with col2:
            st.markdown("**🔒 Privacy**")
            st.caption("Your queries are processed securely. No personal information is stored permanently.")

        with col3:
            st.markdown("**📞 Support**")
            st.caption("For technical issues or feedback, contact the system administrators.")

    def run(self):
        """Main application entry point"""
        self.render_header()
        self.render_sidebar()
        self.render_query_interface()
        self.render_response_display()
        self.render_footer()


def main():
    """Main application function"""
    try:
        app = NSWRevenueAssistantUI()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application failed: {e}")


if __name__ == "__main__":
    main()