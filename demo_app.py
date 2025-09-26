"""
NSW Revenue AI Assistant - Demo Version
Simplified demo without full database setup
"""

import streamlit as st
import os
import time
from datetime import datetime
from typing import Dict, List
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="NSW Revenue AI Assistant - Demo",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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

.demo-box {
    background-color: #fff3cd;
    color: #856404;
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid #ffeaa7;
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

.confidence-high { color: #28a745; }
.confidence-medium { color: #ffc107; }
.confidence-low { color: #dc3545; }
</style>
""", unsafe_allow_html=True)


class DemoNSWRevenueAssistant:
    """Demo version of the NSW Revenue AI Assistant"""

    def __init__(self):
        self._initialize_session_state()
        self.demo_responses = self._load_demo_responses()

    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'demo_queries' not in st.session_state:
            st.session_state.demo_queries = []

        if 'current_demo_response' not in st.session_state:
            st.session_state.current_demo_response = None

    def _load_demo_responses(self) -> Dict:
        """Load pre-configured demo responses"""
        return {
            "payroll tax rate": {
                "query": "What is the current payroll tax rate for wages over $1.2 million?",
                "answer": """Based on the Payroll Tax Act 2007 (NSW), the current payroll tax rate for wages over $1.2 million is **5.45%**.

**Key Details:**
- The payroll tax threshold is $1.2 million annually
- Wages above this threshold are subject to the 5.45% rate
- This applies to employers whose total Australian wages exceed the threshold
- The rate is calculated on wages paid above the tax-free threshold

**Calculation Example:**
If your annual wages are $1.5 million:
- Tax-free threshold: $1.2 million
- Taxable wages: $300,000 ($1.5M - $1.2M)
- Payroll tax: $16,350 ($300,000 × 5.45%)""",
                "citations": [
                    "Payroll Tax Act 2007 (NSW) Section 15",
                    "Payroll Tax Act 2007 (NSW) Section 11(1)",
                    "Revenue NSW Payroll Tax Guidelines 2024"
                ],
                "confidence": 0.92,
                "approved": True,
                "processing_time": 2.3,
                "validation_summary": "✅ Approved | Score: 0.89 | Citations: 1.00 | Facts: 0.95"
            },

            "stamp duty calculation": {
                "query": "How do I calculate stamp duty on an $800,000 residential property?",
                "answer": """For an $800,000 residential property in NSW, the stamp duty calculation under the Duties Act 1997 is:

**Stamp Duty Calculation:**
- $0 - $14,000: $1.25 per $100 = $175
- $14,001 - $32,000: $1.50 per $100 = $270
- $32,001 - $83,000: $1.75 per $100 = $892.50
- $83,001 - $319,000: $3.50 per $100 = $8,260
- $319,001 - $800,000: $4.50 per $100 = $21,645

**Total Stamp Duty: $31,242.50**

**Additional Considerations:**
- First home buyers may be eligible for concessions
- The calculation applies to the greater of purchase price or market value
- Additional charges may apply (e.g., mortgage duty, transfer fees)""",
                "citations": [
                    "Duties Act 1997 (NSW) Section 31",
                    "Duties Act 1997 (NSW) Schedule 2",
                    "First Home Owner Grant (New Homes) Act 2000 (NSW)"
                ],
                "confidence": 0.88,
                "approved": True,
                "processing_time": 2.8,
                "validation_summary": "✅ Approved | Score: 0.85 | Citations: 0.95 | Facts: 0.90"
            },

            "land tax exemption": {
                "query": "What are the land tax exemptions for primary residence?",
                "answer": """Under the Land Tax Act 1956 and Land Tax Management Act 1956 (NSW), your **primary residence is generally exempt** from land tax.

**Primary Residence Exemption:**
- Your principal place of residence is exempt from land tax
- The property must be your main residence
- The exemption applies to the land surrounding the dwelling (up to 2 hectares)
- You can only have one exempt principal place of residence

**Requirements:**
- You must genuinely occupy the property as your home
- The property must be primarily used for residential purposes
- Commercial use may affect the exemption

**Other Exemptions:**
- Pensioner concessions may apply
- Certain rural properties may qualify for exemptions
- Charitable organizations may be exempt

**Note:** Investment properties and second homes are not exempt and are subject to land tax if above the threshold.""",
                "citations": [
                    "Land Tax Management Act 1956 (NSW) Section 10",
                    "Land Tax Act 1956 (NSW) Section 3A",
                    "Revenue NSW Land Tax Guidelines"
                ],
                "confidence": 0.85,
                "approved": True,
                "processing_time": 2.1,
                "validation_summary": "✅ Approved | Score: 0.82 | Citations: 0.90 | Facts: 0.88"
            }
        }

    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">🏛️ NSW Revenue AI Assistant</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Expert guidance on NSW taxation and revenue matters</p>', unsafe_allow_html=True)

        # Demo notice
        st.markdown("""
        <div class="demo-box">
            <strong>🚧 Demo Mode</strong><br>
            This is a demonstration version with pre-configured responses.
            The full version connects to live NSW Revenue legislation database.
        </div>
        """, unsafe_allow_html=True)

    def render_sidebar(self):
        """Render the sidebar with demo options"""
        with st.sidebar:
            st.header("🎯 Demo Queries")

            demo_options = list(self.demo_responses.keys())

            for i, key in enumerate(demo_options):
                response_data = self.demo_responses[key]
                if st.button(f"📝 {response_data['query'][:35]}...", key=f"demo_{i}"):
                    st.session_state.current_demo_response = response_data
                    st.rerun()

            st.divider()

            # System information
            st.header("ℹ️ Demo Features")
            st.info("""
            **Available in Full Version:**
            - Live NSW Revenue legislation search
            - Dual-agent validation system
            - Real-time confidence scoring
            - Citation verification
            - Custom query processing
            """)

            st.header("⚙️ Demo Settings")
            show_validation = st.checkbox("Show Validation Details", value=True)
            show_metadata = st.checkbox("Show Processing Metadata", value=False)

            st.session_state.demo_show_validation = show_validation
            st.session_state.demo_show_metadata = show_metadata

    def render_query_interface(self):
        """Render the demo query interface"""
        st.header("💬 Try the Demo")

        st.info("Select one of the demo queries from the sidebar to see how the NSW Revenue AI Assistant works!")

        # Custom query (limited in demo)
        custom_query = st.text_area(
            "Or enter a custom query (demo will show general response):",
            placeholder="e.g., What is the land tax threshold for 2024?",
            height=100
        )

        if st.button("🚀 Process Demo Query", type="primary", disabled=not custom_query.strip()):
            self._process_custom_demo_query(custom_query.strip())

    def _process_custom_demo_query(self, query: str):
        """Process a custom demo query"""
        # Simulate processing time
        with st.spinner("🤖 Processing through demo system..."):
            time.sleep(1.5)  # Simulate processing

        # Generate demo response
        demo_response = {
            "query": query,
            "answer": f"""Thank you for your query: "{query}"

**Demo Response:**
This is a demonstration of the NSW Revenue AI Assistant. In the full version, this query would be processed through our dual-agent system, which includes:

1. **Document Retrieval**: Searching relevant NSW Revenue legislation
2. **Primary Response**: Generating accurate answers with citations
3. **Approval Validation**: Fact-checking and confidence scoring
4. **Enhanced Response**: Final validated answer with confidence metrics

**For Real NSW Revenue Information:**
Please consult Revenue NSW directly or use the full version of this assistant with access to the complete legislation database.

**Demo Note:** The responses shown in the sidebar demonstrate the actual capabilities of the full system.""",
            "citations": ["Demo Mode - See sidebar for real examples"],
            "confidence": 0.70,
            "approved": True,
            "processing_time": 1.5,
            "validation_summary": "🎯 Demo Response | Limited functionality in demo mode"
        }

        st.session_state.current_demo_response = demo_response
        st.success("✅ Demo query processed")
        st.rerun()

    def render_response_display(self):
        """Render the response display section"""
        if not st.session_state.current_demo_response:
            return

        response = st.session_state.current_demo_response

        st.header("📋 Response")

        # Query display
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f4e79; margin: 1rem 0;">
            <strong>Your Question:</strong><br>
            {response['query']}
        </div>
        """, unsafe_allow_html=True)

        # Validation status
        if st.session_state.get('demo_show_validation', True):
            approval_class = "validation-approved"
            st.markdown(f"""
            <div class="{approval_class}">
                ✅ <strong>Validation Status:</strong> {response['validation_summary']}
            </div>
            """, unsafe_allow_html=True)

        # Main answer
        st.markdown(f"""
        <div class="response-box">
            <h4>💡 Answer</h4>
            {response['answer']}
        </div>
        """, unsafe_allow_html=True)

        # Metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            confidence = response['confidence']
            confidence_class = "confidence-high" if confidence >= 0.7 else "confidence-medium"
            st.markdown(f"""
            <div style="text-align: center;">
                <h4>📊 Confidence</h4>
                <span class="{confidence_class}" style="font-size: 1.5rem; font-weight: bold;">
                    {confidence:.1%}
                </span>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div style="text-align: center;">
                <h4>✅ Status</h4>
                <span style="font-size: 1.2rem; font-weight: bold;">
                    {'Approved' if response['approved'] else 'Review'}
                </span>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div style="text-align: center;">
                <h4>⏱️ Processing</h4>
                <span style="font-size: 1.2rem; font-weight: bold;">
                    {response['processing_time']:.1f}s
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Citations
        if response['citations']:
            st.markdown("### 📚 Legal Citations")
            for i, citation in enumerate(response['citations'], 1):
                st.markdown(f"{i}. {citation}")

        # Metadata
        if st.session_state.get('demo_show_metadata', False):
            with st.expander("🔍 Demo Metadata", expanded=False):
                st.json({
                    "demo_mode": True,
                    "query_processed": response['query'],
                    "confidence_score": response['confidence'],
                    "processing_time": response['processing_time'],
                    "validation_passed": response['approved']
                })

    def render_footer(self):
        """Render the footer"""
        st.divider()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**🎯 Demo Version**")
            st.caption("This demonstrates the NSW Revenue AI Assistant capabilities. Full version includes live legislation database.")

        with col2:
            st.markdown("**⚠️ Disclaimer**")
            st.caption("Demo responses are examples only. For actual legal guidance, consult qualified professionals.")

        with col3:
            st.markdown("**🚀 Full System**")
            st.caption("The complete system includes dual-agent validation, live document search, and real-time processing.")

    def run(self):
        """Main application entry point"""
        self.render_header()
        self.render_sidebar()
        self.render_query_interface()
        self.render_response_display()
        self.render_footer()


def main():
    """Main demo function"""
    try:
        demo_app = DemoNSWRevenueAssistant()
        demo_app.run()
    except Exception as e:
        st.error(f"Demo error: {e}")
        logger.error(f"Demo failed: {e}")


if __name__ == "__main__":
    main()