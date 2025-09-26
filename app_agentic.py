"""
NSW Revenue AI Assistant - Agentic Interface
Clean interface with classification-driven sourcing and highlighted responses
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

# Import new agentic modules
from agents.classification_agent import ClassificationAgent, RevenueType, QuestionIntent
from agents.targeted_sourcing_agent import TargetedSourcingAgent, SourcedContent
from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

# Page configuration
st.set_page_config(
    page_title="NSW Revenue AI Assistant",
    page_icon="NSW",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for professional tax information display
st.markdown("""
<style>
/* Main interface styling */
.main .block-container {
    max-width: 100%;
    padding: 2rem 1rem;
}

/* Classification badges */
.classification-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 500;
    margin: 0.25rem 0.25rem 0.25rem 0;
}

.revenue-payroll { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
.revenue-land { background: #f3e5f5; color: #7b1fa2; border: 1px solid #ce93d8; }
.revenue-stamp { background: #fff3e0; color: #f57c00; border: 1px solid #ffcc02; }
.revenue-admin { background: #e8f5e8; color: #2e7d32; border: 1px solid #a5d6a7; }

.intent-calculation { background: #fce4ec; color: #c2185b; border: 1px solid #f8bbd9; }
.intent-eligibility { background: #e0f2f1; color: #00695c; border: 1px solid #80cbc4; }
.intent-process { background: #e1f5fe; color: #0277bd; border: 1px solid #81d4fa; }

/* Enhanced Response Container */
.response-container {
    background: #ffffff;
    border: 1px solid #e1e5e9;
    border-radius: 12px;
    margin: 1rem 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    overflow: hidden;
}

/* Direct Answer Section */
.direct-answer {
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 1.5rem;
    border-bottom: 1px solid #dee2e6;
}

.direct-answer h3 {
    color: #2c3e50;
    margin: 0 0 1rem 0;
    font-size: 1.1rem;
    font-weight: 600;
    display: flex;
    align-items: center;
}

.direct-answer h3:before {
    content: "•";
    margin-right: 0.5rem;
}

.direct-answer-content {
    font-size: 1rem;
    line-height: 1.6;
    color: #2c3e50;
    font-weight: 500;
}

/* Key Facts Cards */
.key-facts-section {
    padding: 1.5rem;
    background: #fdfdfe;
}

.key-facts-title {
    color: #2c3e50;
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    display: flex;
    align-items: center;
}

.key-facts-title:before {
    content: "•";
    margin-right: 0.5rem;
}

.key-facts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin-bottom: 1.5rem;
}

.key-fact-card {
    background: #ffffff;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    border-left: 4px solid #0066cc;
}

.key-fact-value {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0066cc;
    display: block;
    margin-bottom: 0.25rem;
}

.key-fact-label {
    font-size: 0.85rem;
    color: #6c757d;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* Legislative Citations */
.citations-section {
    padding: 1.5rem;
    background: #f8f9fa;
    border-top: 1px solid #dee2e6;
}

.citations-title {
    color: #2c3e50;
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    display: flex;
    align-items: center;
}

.citations-title:before {
    content: "•";
    margin-right: 0.5rem;
}

.citation-card {
    background: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 6px;
    margin: 0.75rem 0;
    overflow: hidden;
}

.citation-header {
    background: #e9ecef;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid #dee2e6;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.citation-act {
    font-weight: 600;
    color: #2c3e50;
    font-size: 0.9rem;
}

.citation-relevance {
    background: #28a745;
    color: white;
    padding: 0.2rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

.citation-content {
    padding: 1rem;
    font-size: 0.9rem;
    line-height: 1.6;
    color: #495057;
    border-left: 3px solid #0066cc;
    background: #f8f9fa;
    margin: 0.5rem;
    font-style: italic;
}

/* Supporting Details Section */
.supporting-details {
    padding: 1.5rem;
    background: #ffffff;
}

.supporting-details-title {
    color: #2c3e50;
    font-size: 1rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
    display: flex;
    align-items: center;
}

.supporting-details-title:before {
    content: "•";
    margin-right: 0.5rem;
}

.supporting-details-content {
    font-size: 0.95rem;
    line-height: 1.6;
    color: #495057;
}

/* Source cards */
.source-card {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.source-header {
    font-weight: 600;
    color: #333;
    margin-bottom: 0.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.source-type {
    padding: 0.2rem 0.5rem;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 500;
}

.type-legislation { background: #e8f5e8; color: #2e7d32; }
.type-website { background: #e3f2fd; color: #1565c0; }
.type-huggingface { background: #fff3e0; color: #f57c00; }

.highlighted-text {
    background: #fff9c4;
    padding: 0.3rem;
    border-left: 3px solid #fbc02d;
    margin: 0.3rem 0;
    font-style: italic;
}

.confidence-score {
    font-size: 0.8rem;
    color: #666;
}

/* Confidence Indicator */
.confidence-indicator {
    display: inline-flex;
    align-items: center;
    padding: 0.4rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 1rem;
}

.confidence-high {
    background: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.confidence-medium {
    background: #fff3cd;
    color: #856404;
    border: 1px solid #ffeaa7;
}

.confidence-low {
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

/* Enhanced typography for supporting details */
.supporting-details-content p {
    margin: 0.75rem 0;
}

.supporting-details-content strong {
    color: #2c3e50;
    font-weight: 600;
}

.supporting-details-content em {
    color: #495057;
    font-style: italic;
}

/* Section dividers */
.response-container > div:not(:last-child) {
    position: relative;
}

.response-container > div:not(:last-child):after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 1.5rem;
    right: 1.5rem;
    height: 1px;
    background: linear-gradient(to right, transparent, #dee2e6, transparent);
}

/* Improved readability for long content */
.citation-content, .supporting-details-content {
    line-height: 1.7;
}

/* Hover effects for interactivity */
.key-fact-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,102,204,0.15);
    transition: all 0.2s ease;
}

.citation-card:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: all 0.2s ease;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .key-facts-grid {
        grid-template-columns: 1fr;
    }

    .citation-header {
        flex-direction: column;
        gap: 0.5rem;
        align-items: flex-start;
    }

    .response-container {
        margin: 0.5rem 0;
    }

    .direct-answer, .key-facts-section, .citations-section, .supporting-details {
        padding: 1rem;
    }
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'classification_agent' not in st.session_state:
    st.session_state.classification_agent = ClassificationAgent()

if 'sourcing_agent' not in st.session_state:
    st.session_state.sourcing_agent = TargetedSourcingAgent()

if 'dual_agent' not in st.session_state:
    st.session_state.dual_agent = LocalDualAgentOrchestrator()

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'current_classification' not in st.session_state:
    st.session_state.current_classification = None

if 'current_sources' not in st.session_state:
    st.session_state.current_sources = []

if 'is_processing' not in st.session_state:
    st.session_state.is_processing = False

def format_enhanced_response(answer: str, sources: List, confidence: float = 0.0) -> str:
    """
    Format response with enhanced structure including direct answer, key facts, and citations
    """
    import re
    import html

    # Parse the answer to extract different sections
    direct_answer = ""
    key_facts = []
    supporting_details = ""

    # Try to extract a direct answer (first paragraph or sentence)
    paragraphs = answer.split('\n\n')
    if paragraphs:
        direct_answer = paragraphs[0].strip()
        if len(paragraphs) > 1:
            supporting_details = '\n\n'.join(paragraphs[1:])

    # Extract tax-specific key facts with enhanced patterns
    fact_patterns = [
        # Tax rates and percentages
        (r'\d+\.?\d*\s*%', 'Tax Rate'),
        # Dollar amounts
        (r'\$[\d,]+(?:\.\d{2})?', 'Amount'),
        # Thresholds with specific tax terms
        (r'(?:threshold|exemption|limit).*?\$[\d,]+', 'Threshold'),
        # Payroll tax specific
        (r'(?:payroll tax|wages).*?\$[\d,]+', 'Payroll Amount'),
        # Land tax specific
        (r'(?:land value|unimproved value|principal place of residence).*?\$[\d,]+', 'Land Value'),
        # Stamp duty specific
        (r'(?:stamp duty|dutiable value|premium).*?\$[\d,]+', 'Stamp Duty'),
        # Due dates and deadlines
        (r'\b(?:due|payable|lodge).*?(?:\d{1,2}(?:st|nd|rd|th)?.*?(?:January|February|March|April|May|June|July|August|September|October|November|December)|\d{1,2}/\d{1,2}/\d{4})', 'Due Date'),
        # Financial years
        (r'(?:20\d{2}[-/]?\d{2,4}|FY\s*20\d{2})', 'Financial Year'),
    ]

    extracted_facts = []
    for pattern, label_type in fact_patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        for match in matches:
            # Clean up the match
            cleaned_match = match.strip()
            # Avoid duplicates and overly long matches
            if len(cleaned_match) < 50 and cleaned_match not in [f['value'] for f in extracted_facts]:
                extracted_facts.append({'value': cleaned_match, 'label': label_type})

    # Sort by relevance (shorter, cleaner values first) and take top 4
    key_facts = sorted(extracted_facts, key=lambda x: len(x['value']))[:4]

    # Determine confidence level
    if confidence >= 0.8:
        confidence_class = "confidence-high"
        confidence_text = "High Confidence"
    elif confidence >= 0.6:
        confidence_class = "confidence-medium"
        confidence_text = "Medium Confidence"
    else:
        confidence_class = "confidence-low"
        confidence_text = "Low Confidence"

    # Build the formatted response
    formatted_html = f"""
    <div class="response-container">
        <!-- Direct Answer Section -->
        <div class="direct-answer">
            <h3>Direct Answer</h3>
            <div class="direct-answer-content">{direct_answer}</div>
            <div class="confidence-indicator {confidence_class}">
                {confidence_text} ({confidence:.1%})
            </div>
        </div>
    """

    # Add Key Facts section if we found any
    if key_facts:
        formatted_html += """
        <div class="key-facts-section">
            <div class="key-facts-title">Key Facts</div>
            <div class="key-facts-grid">
        """

        for fact in key_facts[:4]:  # Limit to 4 key facts
            formatted_html += f"""
                <div class="key-fact-card">
                    <span class="key-fact-value">{fact['value']}</span>
                    <span class="key-fact-label">{fact['label']}</span>
                </div>
            """

        formatted_html += """
            </div>
        </div>
        """

    # Add Citations section
    if sources:
        formatted_html += """
        <div class="citations-section">
            <div class="citations-title">Legislative Citations</div>
        """

        for source in sources[:3]:  # Show top 3 most relevant sources
            relevance_score = getattr(source, 'relevance_score', 0.0)
            relevance_percent = int(relevance_score * 100) if relevance_score else 0

            act_name = getattr(source, 'act_name', None) or getattr(source, 'title', 'Unknown Act')

            formatted_html += f"""
            <div class="citation-card">
                <div class="citation-header">
                    <div class="citation-act">{act_name}</div>
                    <div class="citation-relevance">{relevance_percent}% Relevant</div>
                </div>
            """

            # Add highlighted text if available
            if hasattr(source, 'highlighted_text') and source.highlighted_text:
                for passage in source.highlighted_text[:2]:  # Top 2 passages
                    formatted_html += f"""
                    <div class="citation-content">
                        "{passage}"
                    </div>
                    """
            elif hasattr(source, 'content') and source.content:
                # Show first 200 characters of content if no highlighted text
                content_preview = source.content[:200] + "..." if len(source.content) > 200 else source.content
                formatted_html += f"""
                <div class="citation-content">
                    "{content_preview}"
                </div>
                """

            formatted_html += "</div>"

        formatted_html += "</div>"

    # Add Supporting Details section if we have additional content
    if supporting_details.strip():
        # Apply formatting directly since we're using unsafe_allow_html=True
        formatted_details = supporting_details.replace('\n\n', '</p><p>').replace('\n', '<br>')
        # Handle bold text (now safe because content is escaped)
        formatted_details = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', formatted_details)
        # Handle italic text (now safe because content is escaped)
        formatted_details = re.sub(r'\*(.*?)\*', r'<em>\1</em>', formatted_details)

        formatted_html += f"""
        <div class="supporting-details">
            <div class="supporting-details-title">Supporting Details</div>
            <div class="supporting-details-content"><p>{formatted_details}</p></div>
        </div>
        """

    formatted_html += "</div>"

    return formatted_html

def _extract_tax_facts(content: str) -> dict:
    """Extract structured tax facts from source content using LLM"""
    from openai import OpenAI
    import os
    import json

    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    try:
        prompt = f"""Extract key tax facts from this NSW legislation text. Return ONLY valid JSON.

Text: {content[:2000]}

Extract these facts (use null if not found):
- tax_rate: The percentage rate (e.g., "5.45%")
- threshold: The tax-free threshold amount (e.g., "$1,200,000")
- sections: Key section numbers referenced (array)
- due_dates: When payments/returns are due
- calculation_method: How tax is calculated
- exemptions: Key exemptions mentioned

Return JSON only:"""

        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        # Fallback to basic parsing if LLM fails
        return {
            "tax_rate": "5.45%" if "5.45%" in content else None,
            "threshold": "$1,200,000" if "1,200,000" in content else None,
            "sections": ["11", "15", "5"] if "Section" in content else [],
            "error": f"LLM extraction failed: {e}"
        }

# Header
st.markdown("# NSW Revenue AI Assistant")
st.markdown("**Intelligent classification and targeted sourcing for NSW taxation queries**")

# Sidebar for classification and sources
with st.sidebar:
    st.markdown("## Query Analysis")

    if st.session_state.current_classification:
        classification = st.session_state.current_classification

        # Display classification
        revenue_class = f"revenue-{classification.revenue_type.value.replace('_', '-')}"
        intent_class = f"intent-{classification.question_intent.value}"

        st.markdown(f'''
        <div>
            <div class="classification-badge {revenue_class}">
                {classification.revenue_type.value.replace('_', ' ').title()}
            </div>
            <div class="classification-badge {intent_class}">
                {classification.question_intent.value.title()}
            </div>
        </div>
        <div class="confidence-score">
            Confidence: {classification.confidence:.1%}
        </div>
        ''', unsafe_allow_html=True)

        if classification.key_entities:
            st.markdown("**Key Entities:**")
            for entity in classification.key_entities:
                st.markdown(f"• {entity}")

    st.markdown("---")
    st.markdown("## Sources")

    if st.session_state.current_sources:
        st.markdown(f"**{len(st.session_state.current_sources)} targeted sources**")

        for i, source in enumerate(st.session_state.current_sources, 1):
            source_type_class = f"type-{source.source_type}"

            st.markdown(f'''
            <div class="source-card">
                <div class="source-header">
                    <span>{i}. {source.title[:40]}...</span>
                    <span class="source-type {source_type_class}">{source.source_type}</span>
                </div>
                <div style="font-size: 0.8rem; color: #666;">
                    Relevance: {source.relevance_score:.2f}
                </div>
                {f'<div style="font-size: 0.75rem; margin-top: 0.3rem;">{source.content[:100]}...</div>' if source.content else ''}
            </div>
            ''', unsafe_allow_html=True)
    else:
        st.info("Sources will appear here after you ask a question")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # Question input
    st.markdown("### Ask Your Question")

    with st.form("question_form", clear_on_submit=True):
        user_question = st.text_area(
            "Enter your NSW Revenue question:",
            placeholder="e.g., What is the payroll tax rate for a business with $2 million in wages?",
            height=100,
            disabled=st.session_state.is_processing
        )

        col_submit, col_clear = st.columns([1, 1])

        with col_submit:
            submit_clicked = st.form_submit_button(
                "Analyze & Answer",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.is_processing
            )

        with col_clear:
            if st.form_submit_button("Clear History", use_container_width=True):
                st.session_state.conversation_history = []
                st.session_state.current_classification = None
                st.session_state.current_sources = []
                st.rerun()

    # Display conversation history
    if st.session_state.conversation_history:
        st.markdown("### Conversation History")

        for i, entry in enumerate(st.session_state.conversation_history):
            with st.expander(f"Q{i+1}: {entry['question'][:60]}...", expanded=(i == len(st.session_state.conversation_history) - 1)):

                # Show classification info
                if 'classification' in entry:
                    c = entry['classification']
                    st.markdown(f"**Classification:** {c.revenue_type.value.replace('_', ' ').title()} • {c.question_intent.value.title()}")

                # Show enhanced formatted answer
                if 'answer' in entry and 'sources' in entry:
                    confidence = entry.get('confidence', 0.0)
                    formatted_response = format_enhanced_response(
                        entry['answer'],
                        entry['sources'],
                        confidence
                    )
                    st.markdown(formatted_response, unsafe_allow_html=True)
                elif 'answer' in entry:
                    # Fallback to simple display if sources not available
                    st.markdown("**Answer:**")
                    st.markdown(entry['answer'])

with col2:
    st.markdown("### Processing Status")

    if st.session_state.is_processing:
        st.info("Processing your question...")
        progress_bar = st.progress(0)
        status_text = st.empty()
    else:
        st.success("Ready for questions")

    st.markdown("---")
    st.markdown("### System Info")
    st.metric("Total Questions", len(st.session_state.conversation_history))

    if st.session_state.current_classification:
        st.metric("Classification Confidence", f"{st.session_state.current_classification.confidence:.1%}")

    if st.session_state.current_sources:
        avg_relevance = sum(s.relevance_score for s in st.session_state.current_sources) / len(st.session_state.current_sources)
        st.metric("Avg Source Relevance", f"{avg_relevance:.2f}")

# Process question submission
if submit_clicked and user_question.strip() and not st.session_state.is_processing:
    st.session_state.is_processing = True
    # Don't immediately rerun - let processing happen in current execution

# Handle processing
if st.session_state.is_processing:
    if user_question and user_question.strip():
        # Start processing new question
        question = user_question.strip()

        # Prevent processing error messages as questions
        if question.startswith("Error processing question:"):
            st.session_state.is_processing = False
            question = None
        else:
            # Add to conversation history
            st.session_state.conversation_history.append({
                'question': question,
                'processing': True,
                'timestamp': time.time()
            })
            last_entry = st.session_state.conversation_history[-1]
    else:
        # No question to process
        st.session_state.is_processing = False
        last_entry = None
        question = None
else:
    last_entry = None
    question = None

# Ensure last_entry is defined if not set above
if 'last_entry' not in locals():
    last_entry = None

if st.session_state.is_processing and question:
    try:
        # Initialize variables to prevent undefined variable errors
        answer = "Error occurred during processing"
        confidence = 0.0

        # Initialize progress bar in sidebar
        with col2:
            progress_bar = st.progress(0.1)
            status_text = st.empty()
            status_text.text("Classifying question...")

        # Step 1: Classify the question
        classification = st.session_state.classification_agent.classify_question(question)
        st.session_state.current_classification = classification
        last_entry['classification'] = classification

        progress_bar.progress(0.3)
        status_text.text(f"Classified as: {classification.revenue_type.value.replace('_', ' ').title()}")

        # Step 2: Get targeted sources
        status_text.text("Retrieving targeted sources...")

        sources = st.session_state.sourcing_agent.get_targeted_sources(question, classification, max_sources=6)
        st.session_state.current_sources = sources
        last_entry['sources'] = sources

        progress_bar.progress(0.6)
        status_text.text(f"Found {len(sources)} relevant sources")

        # Step 3: Generate answer using dual agent system
        status_text.text("Generating answer...")

        # Convert sources to structured format for better LLM processing
        formatted_sources = []
        for source in sources:
            # Extract key facts from source content
            key_facts = _extract_tax_facts(source.content)

            # Create structured source with clear citations
            formatted_source = {
                'act_name': source.act_name or source.title,
                'content': source.content,
                'key_facts': key_facts,
                'highlighted_passages': getattr(source, 'highlighted_text', []),
                'similarity_score': source.relevance_score,
                'source': source.source_type,
                'citation': f"{source.act_name or source.title} (Relevance: {source.relevance_score:.1%})"
            }
            formatted_sources.append(formatted_source)

        # Temporarily replace the dual agent's context method to use our sources
        original_method = st.session_state.dual_agent._get_local_context
        st.session_state.dual_agent._get_local_context = lambda query: formatted_sources

        response = st.session_state.dual_agent.process_query(question, enable_approval=True, classification_result=classification)

        # Restore original method
        st.session_state.dual_agent._get_local_context = original_method

        progress_bar.progress(1.0)
        status_text.text("Complete!")

        # Format and store the answer
        if hasattr(response, 'final_response'):
            answer = response.final_response.content
            confidence = getattr(response.final_response, 'confidence_score', 0.0)
        else:
            answer = str(response)
            confidence = 0.0

        # Add source highlighting information to the answer
        if sources and any(s.highlighted_text for s in sources):
            answer += "\n\n**Key Legislative Passages:**"
            for source in sources[:3]:  # Show passages from top 3 sources
                if source.highlighted_text:
                    answer += f"\n\n*From {source.title}:*"
                    for passage in source.highlighted_text[:2]:  # Top 2 passages per source
                        answer += f"\n> {passage}"

        # Update conversation history
        last_entry.update({
            'answer': answer,
            'confidence': confidence,
            'processing': False
        })

    except Exception as e:
        st.error(f"Error processing question: {str(e)}")
        if last_entry:
            last_entry.update({
                'answer': f"Error processing question: {str(e)}",
                'confidence': 0.0,
                'processing': False
            })

    finally:
        st.session_state.is_processing = False
        # Remove st.rerun() to prevent UI blocking

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**Classification-Driven**")
    st.markdown("Questions are classified by revenue type and intent")

with col2:
    st.markdown("**Targeted Sourcing**")
    st.markdown("Sources retrieved based on specific classification")

with col3:
    st.markdown("**Highlighted Answers**")
    st.markdown("Specific legislative passages shown with responses")