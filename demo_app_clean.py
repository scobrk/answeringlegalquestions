"""
NSW Revenue AI Assistant - Professional Demo
Clean, professional UI without emojis, shadcn-inspired design
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
    page_title="NSW Revenue AI Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Shadcn-inspired CSS with clean, professional design
st.markdown("""
<style>
/* Root variables - shadcn inspired */
:root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: 222.2 84% 4.9%;
    --radius: 0.5rem;
}

/* Typography */
.main-header {
    font-size: 2rem;
    font-weight: 600;
    color: hsl(var(--foreground));
    margin-bottom: 0.5rem;
    letter-spacing: -0.025em;
}

.sub-header {
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
    margin-bottom: 2rem;
}

/* Card component */
.card {
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
}

.card-header {
    font-size: 1.125rem;
    font-weight: 600;
    color: hsl(var(--card-foreground));
    margin-bottom: 0.5rem;
}

.card-description {
    font-size: 0.875rem;
    color: hsl(var(--muted-foreground));
    line-height: 1.5;
}

/* Alert components */
.alert {
    padding: 1rem;
    border-radius: var(--radius);
    border: 1px solid;
    margin: 1rem 0;
    font-size: 0.875rem;
}

.alert-warning {
    background: hsl(47.9 95.8% 96.1%);
    border-color: hsl(47.9 95.8% 76.1%);
    color: hsl(47.9 95.8% 16.1%);
}

.alert-success {
    background: hsl(142.1 76.2% 96.3%);
    border-color: hsl(142.1 76.2% 76.3%);
    color: hsl(142.1 76.2% 16.3%);
}

.alert-destructive {
    background: hsl(0 84.2% 96.2%);
    border-color: hsl(0 84.2% 76.2%);
    color: hsl(0 84.2% 16.2%);
}

/* Badge component */
.badge {
    display: inline-flex;
    align-items: center;
    border-radius: 9999px;
    padding: 0.25rem 0.625rem;
    font-size: 0.75rem;
    font-weight: 600;
    line-height: 1;
    white-space: nowrap;
}

.badge-default {
    background: hsl(var(--secondary));
    color: hsl(var(--secondary-foreground));
}

.badge-success {
    background: hsl(142.1 76.2% 90.3%);
    color: hsl(142.1 76.2% 16.3%);
}

.badge-warning {
    background: hsl(47.9 95.8% 90.1%);
    color: hsl(47.9 95.8% 16.1%);
}

/* Button styling */
.stButton > button {
    background: hsl(var(--primary));
    color: hsl(var(--primary-foreground));
    border: none;
    border-radius: var(--radius);
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    font-weight: 500;
    transition: opacity 0.2s;
}

.stButton > button:hover {
    opacity: 0.9;
}

/* Input fields */
.stTextArea > div > div > textarea {
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
    font-size: 0.875rem;
}

/* Metrics display */
.metric-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 1rem;
    background: hsl(var(--card));
    border: 1px solid hsl(var(--border));
    border-radius: var(--radius);
}

.metric-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: hsl(var(--muted-foreground));
    text-transform: uppercase;
    letter-spacing: 0.025em;
    margin-bottom: 0.25rem;
}

.metric-value {
    font-size: 1.5rem;
    font-weight: 600;
    color: hsl(var(--foreground));
}

/* Remove Streamlit defaults */
.css-1d391kg {
    padding-top: 2rem;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


class ProfessionalNSWRevenueAssistant:
    """Professional demo version of the NSW Revenue AI Assistant"""

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
            "payroll_tax": {
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
                "validation_summary": "Approved | Score: 0.89 | Citations: 1.00 | Facts: 0.95"
            },

            "stamp_duty": {
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
- Additional charges may apply (mortgage duty, transfer fees)""",
                "citations": [
                    "Duties Act 1997 (NSW) Section 31",
                    "Duties Act 1997 (NSW) Schedule 2",
                    "First Home Owner Grant (New Homes) Act 2000 (NSW)"
                ],
                "confidence": 0.88,
                "approved": True,
                "processing_time": 2.8,
                "validation_summary": "Approved | Score: 0.85 | Citations: 0.95 | Facts: 0.90"
            },

            "land_tax": {
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
                "validation_summary": "Approved | Score: 0.82 | Citations: 0.90 | Facts: 0.88"
            }
        }

    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">NSW Revenue AI Assistant</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-header">Professional guidance on NSW taxation and revenue matters</p>', unsafe_allow_html=True)

        # Demo notice
        st.markdown("""
        <div class="alert alert-warning">
            <strong>Demo Mode</strong><br>
            This is a demonstration version with pre-configured responses.
            The full version connects to live NSW Revenue legislation database.
        </div>
        """, unsafe_allow_html=True)

    def render_sidebar(self):
        """Render the sidebar with demo options"""
        with st.sidebar:
            st.markdown("### Demo Queries")

            demo_options = {
                "payroll_tax": "Payroll Tax Rate Query",
                "stamp_duty": "Stamp Duty Calculation",
                "land_tax": "Land Tax Exemptions"
            }

            for key, label in demo_options.items():
                if st.button(label, key=f"demo_{key}", use_container_width=True):
                    st.session_state.current_demo_response = self.demo_responses[key]
                    st.rerun()

            st.divider()

            st.markdown("### System Features")
            st.markdown("""
            **Available in Full Version:**
            - Live NSW Revenue legislation search
            - Dual-agent validation system
            - Real-time confidence scoring
            - Citation verification
            - Custom query processing
            """)

            st.markdown("### Settings")
            show_validation = st.checkbox("Show Validation Details", value=True)
            show_metadata = st.checkbox("Show Processing Metadata", value=False)

            st.session_state.demo_show_validation = show_validation
            st.session_state.demo_show_metadata = show_metadata

    def render_query_interface(self):
        """Render the demo query interface"""
        st.markdown("### Submit Query")

        st.info("Select a demo query from the sidebar or enter a custom query below.")

        # Custom query
        custom_query = st.text_area(
            "Query:",
            placeholder="Enter your NSW Revenue question...",
            height=100,
            label_visibility="collapsed"
        )

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Process Query", type="primary", disabled=not custom_query.strip()):
                self._process_custom_demo_query(custom_query.strip())

    def _process_custom_demo_query(self, query: str):
        """Process a custom demo query"""
        with st.spinner("Processing query..."):
            time.sleep(1.5)  # Simulate processing

        # Generate demo response
        demo_response = {
            "query": query,
            "answer": f"""**Demo Response for:** "{query}"

This is a demonstration of the NSW Revenue AI Assistant. In the full version, this query would be processed through:

1. **Document Retrieval**: Searching relevant NSW Revenue legislation
2. **Primary Response**: Generating accurate answers with citations
3. **Approval Validation**: Fact-checking and confidence scoring
4. **Enhanced Response**: Final validated answer with confidence metrics

For actual NSW Revenue information, please use the full version with access to the complete legislation database.""",
            "citations": ["Demo Mode - See sidebar for real examples"],
            "confidence": 0.70,
            "approved": True,
            "processing_time": 1.5,
            "validation_summary": "Demo Response | Limited functionality"
        }

        st.session_state.current_demo_response = demo_response
        st.success("Query processed successfully")
        st.rerun()

    def render_response_display(self):
        """Render the response display section"""
        if not st.session_state.current_demo_response:
            return

        response = st.session_state.current_demo_response

        # Query card
        st.markdown(f"""
        <div class="card">
            <div class="card-header">Query</div>
            <div class="card-description">{response['query']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Validation status
        if st.session_state.get('demo_show_validation', True):
            if response['approved']:
                st.markdown(f"""
                <div class="alert alert-success">
                    <strong>Validation Status:</strong> {response['validation_summary']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="alert alert-warning">
                    <strong>Validation Status:</strong> {response['validation_summary']}
                </div>
                """, unsafe_allow_html=True)

        # Main answer
        st.markdown(f"""
        <div class="card">
            <div class="card-header">Response</div>
            <div class="card-description">{response['answer']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            confidence = response['confidence']
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Confidence</div>
                <div class="metric-value">{confidence:.1%}</div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            status_text = "Approved" if response['approved'] else "Review"
            badge_class = "badge-success" if response['approved'] else "badge-warning"
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Status</div>
                <div class="badge {badge_class}" style="margin-top: 0.5rem;">{status_text}</div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-label">Processing Time</div>
                <div class="metric-value">{response['processing_time']:.1f}s</div>
            </div>
            """, unsafe_allow_html=True)

        # Citations
        if response['citations']:
            st.markdown("### Legal Citations")
            citation_html = "<ul style='font-size: 0.875rem; color: hsl(var(--muted-foreground));'>"
            for citation in response['citations']:
                citation_html += f"<li>{citation}</li>"
            citation_html += "</ul>"
            st.markdown(citation_html, unsafe_allow_html=True)

        # Metadata
        if st.session_state.get('demo_show_metadata', False):
            with st.expander("Processing Metadata"):
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
            st.markdown("**Demo Version**")
            st.caption("Full system includes live legislation database")

        with col2:
            st.markdown("**Disclaimer**")
            st.caption("For actual legal guidance, consult qualified professionals")

        with col3:
            st.markdown("**System Architecture**")
            st.caption("Dual-agent validation with real-time processing")

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
        app = ProfessionalNSWRevenueAssistant()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        logger.error(f"Application failed: {e}")


if __name__ == "__main__":
    main()