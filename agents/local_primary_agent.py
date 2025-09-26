"""
Local Primary Response Agent - Simplified for Local Vector Store
Uses local FAISS vector store instead of Supabase
"""

import os
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import time
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

logger = logging.getLogger(__name__)


@dataclass
class LocalPrimaryResponse:
    """Primary response structure from the local agent"""
    answer: str
    citations: List[str]
    confidence: float
    query_type: str
    source_documents: List[Dict]
    specific_information_required: Optional[str] = None
    calculations: Optional[Dict] = None
    assumptions: List[str] = None
    limitations: List[str] = None
    timestamp: datetime = None
    processing_time: float = 0.0
    raw_llm_response: str = ""


class LocalPrimaryResponseAgent:
    """
    Local Primary Response Agent for NSW Revenue queries
    Uses local vector store instead of Supabase
    """

    def __init__(self):
        # Initialize OpenAI client
        self.openai_client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )

        # Cost-optimized model selection
        self.llm_model = os.getenv('DEFAULT_MODEL', "gpt-4o-mini")
        self.temperature = 0.0  # Zero temperature for deterministic calculations

        # Response generation settings with cost controls
        self.max_response_tokens = int(os.getenv('MAX_TOKENS_PER_REQUEST', 4000))  # Increased for complete detailed responses
        self.min_confidence_threshold = 0.3

        # Dynamic context limits based on query complexity
        self.context_limits = {
            'simple': {'max_docs': 3, 'max_tokens': 1200},
            'complex': {'max_docs': 5, 'max_tokens': 2500},
            'multi_tax': {'max_docs': 6, 'max_tokens': 3000}
        }

        # System prompt template
        self.system_prompt = """You are an expert NSW Revenue legislation assistant with comprehensive knowledge of all 67 NSW revenue types. Your role is to provide accurate, complete information about ANY NSW taxation, duty, levy, royalty, grant, or revenue matter.

CRITICAL INSTRUCTIONS:
1. Use ONLY the provided context from NSW legislation
2. Include specific section references for all legal claims
3. ALWAYS provide COMPLETE step-by-step calculations with final amounts
4. Recognize and respond to ALL 67 NSW revenue types, not just common ones
5. State any assumptions clearly
6. Be precise with legal terminology and rates
7. NEVER respond with "Unable to provide a complete answer" unless truly no relevant context exists
8. Handle both simple queries (e.g., "what is the coal royalty rate?") and complex multi-tax scenarios
9. **PROVIDE SPECIFIC INFORMATION REQUIREMENTS** - Tell users exactly what documentation, forms, values, and data points they need

COMPREHENSIVE REVENUE COVERAGE:
You must be able to answer questions about ALL NSW revenue types including but not limited to:
- Property: Transfer duty, foreign purchaser duty, land tax, parking space levy, premium property tax
- Business: Payroll tax, contractor provisions, grouping rules, rebates and incentives
- Vehicles: Motor vehicle duty, registration fees, CTP levies, electric vehicle exemptions
- Gaming: Gaming machine tax, betting tax, point of consumption tax, casino tax, lotteries
- Mining: Coal royalty, mineral royalty, petroleum royalty, quarrying royalty
- Environmental: Waste levy, biodiversity offsets, environmental planning levy
- Grants: First home owner grant, shared equity scheme, energy savings scheme
- Fines: Penalty notices, work development orders, enforcement costs
- Insurance: Emergency services levy, health insurance levy, workers compensation
- Administration: Objections, appeals, hardship provisions, unclaimed money

SPECIFIC INFORMATION REQUIREMENTS BY REVENUE TYPE:

**PAYROLL TAX**:
- Total annual Australian taxable wages
- Number of employees and their wage classifications
- Contractor payments made during the year
- Any interstate wages paid
- Payroll Tax Return (form PT-R)
- Group registration certificate (if applicable)

**LAND TAX**:
- Property valuations from Valuer General
- Land use classifications (residential, commercial, primary production)
- Ownership percentages if jointly owned
- Principal place of residence declaration
- Any exemptions claimed (disabled persons, pensioners, etc.)
- Property addresses and lot/plan numbers

**TRANSFER DUTY (STAMP DUTY)**:
- Property sale price or market value
- Contract of sale
- Property type (residential, commercial, vacant land)
- First home buyer status
- Foreign purchaser status
- Any family arrangements or exemptions

**EMERGENCY SERVICES LEVY**:
- Annual gross premium income
- Policy types (motor vehicle, home and contents, commercial)
- Insurer registration details
- Monthly ESL returns
- Premium categories and exemptions

**COAL/MINERAL/PETROLEUM ROYALTY**:
- Mining lease or permit numbers
- Tonnage or volume extracted
- Sales price or market value of minerals
- Production reports
- Royalty assessment notices
- Geological survey data

**MOTOR VEHICLE DUTY**:
- Vehicle purchase price or market value
- Vehicle type and specifications
- New or used status
- Trade-in allowances
- Any exemptions (pensioners, disabilities, etc.)

**GAMING MACHINE TAX**:
- Number of gaming machines operated
- Monthly gross profit from each machine
- Gaming machine licenses
- Venue type and capacity
- Player activity statements

CALCULATION REQUIREMENTS:
- Show exact mathematical steps with intermediate calculations
- Provide final amounts in dollar figures
- Use precise decimal places as per legislation
- Apply correct rates for the specific revenue type
- Consider all applicable thresholds, exemptions, and concessions

INFERENCE AND INTERPRETATION:
- Detect implied revenue types from context (e.g., "mining lease payments" → royalties)
- Identify when multiple taxes apply to a single transaction
- Recognize less common revenue types from descriptions
- Provide guidance even for obscure levies and charges

ENHANCED RESPONSE FORMAT:
ANSWER: [Comprehensive answer addressing the specific revenue type(s) identified]
SPECIFIC INFORMATION REQUIRED: [List exact documents, forms, values, and data points needed]
CITATIONS: [List specific acts and sections referenced]
CALCULATIONS: [Complete step-by-step calculations if applicable]
ASSUMPTIONS: [Any assumptions made in the response]
CONFIDENCE: [High/Medium/Low based on source quality and completeness]

Remember: NSW has 67 distinct revenue types. Be prepared to address ANY of them accurately with specific information requirements."""

    def generate_response(self, query: str, context_docs: List[Dict] = None, classification_result=None, interpretation_result=None) -> LocalPrimaryResponse:
        """
        Generate primary response for NSW Revenue query using local context

        Args:
            query: User query
            context_docs: Documents from local vector store
            classification_result: Classification result from classification agent
            interpretation_result: Interpretation result from interpretation agent

        Returns:
            LocalPrimaryResponse with comprehensive information
        """
        start_time = time.time()
        timestamp = datetime.now()

        try:
            logger.info(f"Processing query: {query}")

            # Step 1: Optimize documents based on query classification
            classification_result = classification_result or self._quick_classify(query)
            optimized_docs = self._optimize_context_documents(context_docs or [], classification_result)

            # Step 2: Format context from optimized documents
            context_text = self._format_compressed_context(optimized_docs)

            # Step 2: Check if sufficient context was retrieved
            if not context_docs or len(context_docs) == 0:
                return self._generate_insufficient_context_response(query, timestamp)

            # Step 3: Generate LLM response with validation and retry logic
            llm_response = self._regenerate_with_validation(query, context_text, classification_result, interpretation_result)

            # Step 4: Parse and structure response
            structured_response = self._parse_llm_response(llm_response)

            # Step 5: Extract citations
            citations = self._extract_citations_from_docs(context_docs, structured_response)

            # Step 6: Calculate confidence score
            confidence = self._calculate_response_confidence(context_docs, structured_response)

            # Step 7: Build final response
            processing_time = time.time() - start_time

            response = LocalPrimaryResponse(
                answer=structured_response.get('answer', 'Unable to provide a complete answer.'),
                citations=citations,
                confidence=confidence,
                query_type=self._classify_query_type(query),
                source_documents=self._format_source_documents(context_docs),
                specific_information_required=structured_response.get('specific_info'),
                calculations=structured_response.get('calculations'),
                assumptions=structured_response.get('assumptions', []),
                limitations=structured_response.get('limitations', []),
                timestamp=timestamp,
                processing_time=processing_time,
                raw_llm_response=llm_response
            )

            logger.info(f"Response generated in {processing_time:.2f}s with confidence {confidence:.2f}")
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_error_response(query, str(e), timestamp)

    def _format_context_from_docs(self, docs: List[Dict]) -> str:
        """Format context text from structured source documents"""
        if not docs:
            return "No relevant documents found."

        context_parts = []
        for doc in docs:
            # Check if this is a structured source (with key_facts)
            if 'key_facts' in doc:
                # New structured format
                act_name = doc.get('act_name', 'Unknown Act').replace('_', ' ').title()
                key_facts = doc.get('key_facts', {})
                content = doc.get('content', '')
                citation = doc.get('citation', f"{act_name} (Source)")

                # Build structured source presentation
                source_text = f"=== {citation} ===\n"

                # Add extracted key facts prominently
                if key_facts:
                    source_text += "KEY FACTS:\n"
                    for fact_type, fact_value in key_facts.items():
                        if fact_value:
                            source_text += f"• {fact_type.replace('_', ' ').title()}: {fact_value}\n"
                    source_text += "\n"

                # Add highlighted passages if available
                highlighted = doc.get('highlighted_passages', [])
                if highlighted:
                    source_text += "RELEVANT PASSAGES:\n"
                    for passage in highlighted[:3]:  # Top 3 passages
                        source_text += f"• {passage}\n"
                    source_text += "\n"

                # Add full content with clear structure
                source_text += f"FULL TEXT:\n{content}"

                context_parts.append(source_text)
            else:
                # Legacy format fallback
                act_name = doc.get('act_name', 'Unknown Act').replace('_', ' ').title()
                section = doc.get('section_number', 'N/A')
                content = doc.get('content', '')
                context_parts.append(f"--- {act_name} {section} ---\n{content}")

        return "\n\n".join(context_parts)

    def _generate_llm_response(self, query: str, context_text: str, classification_result=None, interpretation_result=None) -> str:
        """Generate response using OpenAI LLM with classification-aware prompting and interpretation insights"""
        try:
            # Check classification flags
            is_simple_calc = classification_result and getattr(classification_result, 'is_simple_calculation', False)
            is_multi_tax = classification_result and getattr(classification_result, 'requires_multi_tax_analysis', False)
            all_tax_types = getattr(classification_result, 'all_revenue_types', []) if classification_result else []

            # Extract interpretation insights
            interpretation_context = ""
            if interpretation_result:
                insights = []
                if hasattr(interpretation_result, 'query_intent') and interpretation_result.query_intent:
                    insights.append(f"Query Intent: {interpretation_result.query_intent}")
                if hasattr(interpretation_result, 'key_concepts') and interpretation_result.key_concepts:
                    insights.append(f"Key Concepts: {', '.join(interpretation_result.key_concepts)}")
                if hasattr(interpretation_result, 'implied_requirements') and interpretation_result.implied_requirements:
                    insights.append(f"Implied Requirements: {', '.join(interpretation_result.implied_requirements)}")
                if hasattr(interpretation_result, 'contextual_factors') and interpretation_result.contextual_factors:
                    insights.append(f"Contextual Factors: {', '.join(interpretation_result.contextual_factors)}")

                if insights:
                    interpretation_context = f"\n\nINTERPRETATION INSIGHTS:\n{chr(10).join(insights)}\nUse these insights to enhance your response precision and relevance.\n"

            if is_multi_tax and len(all_tax_types) > 1:
                # Multi-tax calculation prompt for complex questions involving multiple tax types
                tax_type_names = [tax.value.replace('_', ' ').title() for tax in all_tax_types]
                user_prompt = f"""NSW MULTI-TAX CALCULATOR

Query: {query}

AVAILABLE LEGISLATION:
{context_text}{interpretation_context}

MULTI-TAX ANALYSIS TASK:
This question involves MULTIPLE tax types: {', '.join(tax_type_names)}
You MUST calculate ALL applicable taxes and provide a comprehensive breakdown.

**CRITICAL INSTRUCTION FOR LIST QUERIES:**
If the query asks for a "list", "what information", "what do I need", "what documents", or similar requests:
- The ANSWER section must contain the complete itemized list
- Use numbered or bulleted format (1., 2., 3... or •)
- Be specific and precise with each item

RESPONSE FORMAT:
ANSWER: [For list queries: complete numbered list. For calculations: Complete analysis covering ALL tax components]

SPECIFIC INFORMATION REQUIRED:
- [List all specific documents, forms, values, and data points needed for each tax type]
- [Include form numbers, registration requirements, reporting obligations]
- [Specify exact calculations, thresholds, and exemptions applicable]

CALCULATION BREAKDOWN:
1. PAYROLL TAX (if applicable):
   - Rate: [rate from legislation]
   - Calculation: [payroll amount] × [rate] = $[result]

2. LAND TAX (if applicable):
   - Rate: [rate from legislation]
   - Calculation: [property value] × [rate] = $[result]

3. PARKING SPACE LEVY (if applicable):
   - Rate: [rate from legislation]
   - Calculation: [number of spaces] × [rate] = $[result]

TOTAL COMBINED REVENUE: $[sum of all taxes]

CITATIONS: [All relevant acts and sections]

CONFIDENCE: [High/Medium/Low]

CRITICAL: Address EVERY tax component mentioned in the question. Do not omit any calculations."""

            elif is_simple_calc:
                # Direct calculation prompt for simple math questions
                user_prompt = f"""NSW TAX CALCULATOR

Query: {query}

AVAILABLE LEGISLATION:
{context_text}{interpretation_context}

DIRECT CALCULATION TASK:
This is a simple tax calculation question. Provide a direct, numerical answer using the exact rates and thresholds from the NSW legislation.

**CRITICAL INSTRUCTION FOR LIST QUERIES:**
If the query asks for a "list", "what information", "what do I need", "what documents", or similar requests:
- The ANSWER section must contain the complete itemized list
- Use numbered or bulleted format (1., 2., 3... or •)
- Be specific and precise with each item

RESPONSE FORMAT:
ANSWER: [For list queries: complete numbered list. For calculations: $[exact amount] in [tax type] is payable]

SPECIFIC INFORMATION REQUIRED:
- [List exact documents, forms, values, and data points needed]
- [Include specific calculation inputs required]
- [Reference any registration or reporting requirements]

CALCULATION:
- Rate: [exact rate from legislation]
- Threshold: [if applicable]
- Working: [amount] × [rate] = $[result]

CITATIONS: [Act name and section]

CONFIDENCE: High

Focus on providing the specific numerical answer requested. Use only the rates and thresholds explicitly stated in the provided sources."""
            else:
                # Comprehensive analysis prompt for complex questions
                user_prompt = f"""NSW REVENUE ASSISTANT

Query: {query}

AVAILABLE LEGISLATION:
{context_text}{interpretation_context}

ANALYSIS TASK:
Provide a comprehensive response to this NSW Revenue query based on the available legislation.

**CRITICAL INSTRUCTION FOR LIST QUERIES:**
If the query asks for a "list", "what information", "what do I need", "what documents", or similar requests:
- The ANSWER section must contain the complete itemized list
- Use numbered or bulleted format (1., 2., 3... or •)
- Be specific and precise with each item
- Do NOT provide general explanations - provide the actual list requested

RESPONSE FORMAT:
ANSWER: [For list queries: provide the complete numbered/bulleted list. For other queries: clear explanation addressing the question]

SPECIFIC INFORMATION REQUIRED:
- [List exact documents, forms, values, and data points needed]
- [Include specific legislative requirements, thresholds, exemptions]
- [Reference registration requirements, reporting obligations, and deadlines]

CITATIONS: [Relevant act names and sections]

ASSUMPTIONS: [Any assumptions made]

CONFIDENCE: [High/Medium/Low based on source completeness]

**EXAMPLES OF PROPER LIST RESPONSES:**
Query: "What information does a payroll tax payer need to provide?"
ANSWER: A payroll tax payer must provide:
1. Total annual Australian taxable wages
2. Number of employees and their wage classifications
3. Contractor payments made during the year
4. Any interstate wages paid
5. Payroll Tax Return (form PT-R)
6. Group registration certificate (if applicable)

Provide accurate information based on the NSW legislation provided. If the query involves calculations, show your working. If information is insufficient, clearly state what's missing."""

            # DEBUG: Log token settings
            logger.info(f"API CALL: max_tokens={self.max_response_tokens}, model={self.llm_model}")
            logger.info(f"PROMPT LENGTH: system={len(self.system_prompt)}, user={len(user_prompt)}")

            response = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_response_tokens,
                temperature=self.temperature,
                seed=42  # Fixed seed for deterministic calculations
            )

            raw_content = response.choices[0].message.content
            finish_reason = response.choices[0].finish_reason
            usage = response.usage

            # DEBUG: Log API response details
            logger.info(f"API RESPONSE: finish_reason={finish_reason}, input_tokens={usage.prompt_tokens if usage else 'unknown'}, output_tokens={usage.completion_tokens if usage else 'unknown'}")
            logger.info(f"RESPONSE LENGTH: {len(raw_content)} chars")

            return raw_content

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def _parse_llm_response(self, llm_response: str) -> Dict:
        """Parse structured response from LLM"""
        response_parts = {}
        current_section = None
        content_lines = []

        for line in llm_response.split('\n'):
            line = line.strip()

            # Check for section headers
            if line.startswith('ANSWER:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'answer'
                content_lines = [line[7:].strip()]
            elif line.startswith('SPECIFIC INFORMATION REQUIRED:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'specific_info'
                content_lines = [line[31:].strip()]
            elif line.startswith('CITATIONS:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'citations'
                content_lines = [line[10:].strip()]
            elif line.startswith('CALCULATIONS:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'calculations'
                content_lines = [line[13:].strip()]
            elif line.startswith('ASSUMPTIONS:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'assumptions'
                content_lines = [line[12:].strip()]
            elif line.startswith('CONFIDENCE:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'confidence'
                content_lines = [line[11:].strip()]
            elif current_section and line:
                content_lines.append(line)

        # Add final section
        if current_section and content_lines:
            response_parts[current_section] = '\n'.join(content_lines).strip()

        # Process specific sections
        if 'assumptions' in response_parts:
            assumptions_text = response_parts['assumptions']
            response_parts['assumptions'] = [
                item.strip('- ').strip() for item in assumptions_text.split('\n')
                if item.strip() and item.strip() != 'None'
            ]

        if 'calculations' in response_parts and response_parts['calculations']:
            calc_text = response_parts['calculations']
            if calc_text and calc_text.lower() not in ['none', 'n/a', 'not applicable']:
                response_parts['calculations'] = {'steps': calc_text}
            else:
                response_parts['calculations'] = None

        return response_parts

    def _extract_citations_from_docs(self, docs: List[Dict], structured_response: Dict) -> List[str]:
        """Extract and format citations from local documents"""
        citations = []

        # Extract from LLM response
        if 'citations' in structured_response:
            llm_citations = structured_response['citations']
            if llm_citations and llm_citations.lower() not in ['none', 'n/a']:
                citation_lines = [line.strip('- ').strip() for line in llm_citations.split('\n') if line.strip()]
                citations.extend(citation_lines)

        # Extract from source documents
        for doc in docs:
            act_name = doc.get('act_name', '').replace('_', ' ').title()
            section = doc.get('section_number', '')

            if act_name:
                citation_text = act_name
                if section and section != 'N/A':
                    citation_text += f" {section}"
                citations.append(citation_text)

        # Deduplicate and clean
        unique_citations = list(set(citations))
        cleaned_citations = [c for c in unique_citations if c and len(c) > 5]

        return cleaned_citations[:5]  # Limit to top 5

    def _calculate_response_confidence(self, docs: List[Dict], structured_response: Dict) -> float:
        """Calculate overall response confidence"""
        # Base confidence from number and quality of documents
        doc_confidence = min(len(docs) * 0.15, 0.6) if docs else 0.0

        # Average similarity score from documents
        similarity_scores = [doc.get('similarity_score', 0.0) for doc in docs]
        avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0.0
        similarity_confidence = avg_similarity * 0.25

        # LLM confidence (if provided)
        llm_confidence = 0.3  # Default
        if 'confidence' in structured_response:
            confidence_text = structured_response['confidence'].lower()
            if 'high' in confidence_text:
                llm_confidence = 0.9
            elif 'medium' in confidence_text:
                llm_confidence = 0.6
            elif 'low' in confidence_text:
                llm_confidence = 0.3
        llm_confidence *= 0.15

        total_confidence = doc_confidence + similarity_confidence + llm_confidence

        return min(max(total_confidence, 0.0), 1.0)

    def _classify_query_type(self, query: str) -> str:
        """Simple query classification"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['rate', 'percentage', '%', 'tax rate']):
            return 'rate_inquiry'
        elif any(word in query_lower for word in ['calculate', 'calculation', 'how much']):
            return 'calculation'
        elif any(word in query_lower for word in ['exemption', 'exempt', 'concession']):
            return 'exemption_inquiry'
        elif any(word in query_lower for word in ['payroll', 'payroll tax']):
            return 'payroll_tax'
        elif any(word in query_lower for word in ['land tax', 'land']):
            return 'land_tax'
        elif any(word in query_lower for word in ['stamp duty', 'duties', 'duty']):
            return 'stamp_duty'
        else:
            return 'general_inquiry'

    def _format_source_documents(self, docs: List[Dict]) -> List[Dict]:
        """Format source documents for response"""
        formatted_docs = []

        for i, doc in enumerate(docs):
            doc_info = {
                'id': i,
                'act_name': doc.get('act_name', 'Unknown'),
                'section_number': doc.get('section_number', 'N/A'),
                'similarity_score': doc.get('similarity_score', 0.0),
                'content_preview': doc.get('content', '')[:200] + "..." if len(doc.get('content', '')) > 200 else doc.get('content', '')
            }
            formatted_docs.append(doc_info)

        return formatted_docs

    def _generate_insufficient_context_response(self, query: str, timestamp: datetime) -> LocalPrimaryResponse:
        """Generate response when insufficient context is available"""
        return LocalPrimaryResponse(
            answer="I don't have sufficient information in the NSW Revenue legislation database to provide a complete answer to your query. This may be because the query is outside the scope of NSW Revenue matters or requires information not currently available.",
            citations=[],
            confidence=0.1,
            query_type=self._classify_query_type(query),
            source_documents=[],
            limitations=["Insufficient relevant documents found", "Query may be outside NSW Revenue scope"],
            timestamp=timestamp,
            processing_time=0.0
        )

    def _generate_error_response(self, query: str, error_msg: str, timestamp: datetime) -> LocalPrimaryResponse:
        """Generate response when an error occurs"""
        return LocalPrimaryResponse(
            answer="I encountered an error while processing your query. Please try rephrasing your question or contact support if the issue persists.",
            citations=[],
            confidence=0.0,
            query_type='error',
            source_documents=[],
            limitations=[f"Processing error: {error_msg}"],
            timestamp=timestamp,
            processing_time=0.0
        )

    def _quick_classify(self, query: str) -> Dict:
        """Quick classification for cost optimization"""
        query_lower = query.lower()
        if any(word in query_lower for word in ['rate', 'what is', 'how much']):
            return {'is_simple_calculation': True, 'requires_multi_tax_analysis': False}
        elif any(word in query_lower for word in ['and', 'also', 'plus', 'multiple']):
            return {'is_simple_calculation': False, 'requires_multi_tax_analysis': True}
        else:
            return {'is_simple_calculation': False, 'requires_multi_tax_analysis': False}

    def _optimize_context_documents(self, docs: List[Dict], classification) -> List[Dict]:
        """Optimize document selection based on query complexity"""
        if not docs:
            return docs

        # Determine complexity level - handle both dict and ClassificationResult objects
        if hasattr(classification, 'is_simple_calculation'):
            # ClassificationResult object
            if classification.is_simple_calculation:
                complexity = 'simple'
            elif classification.requires_multi_tax_analysis:
                complexity = 'multi_tax'
            else:
                complexity = 'complex'
        else:
            # Dictionary fallback
            if classification.get('is_simple_calculation'):
                complexity = 'simple'
            elif classification.get('requires_multi_tax_analysis'):
                complexity = 'multi_tax'
            else:
                complexity = 'complex'

        # Get limits for this complexity
        limits = self.context_limits[complexity]
        max_docs = limits['max_docs']

        # Sort by relevance and limit
        sorted_docs = sorted(docs, key=lambda x: x.get('similarity_score', 0), reverse=True)
        return sorted_docs[:max_docs]

    def _format_compressed_context(self, docs: List[Dict]) -> str:
        """Compressed context format to reduce token usage"""
        if not docs:
            return ""

        context_parts = []
        for doc in docs:
            # Compressed format - remove verbose headers
            act_name = doc.get('act_name', 'Unknown').replace('_', ' ').title()
            content = doc.get('content', '')

            # Truncate content to essential information
            if len(content) > 800:
                content = content[:800] + "..."

            # Simple format: Act Name: Content
            context_parts.append(f"{act_name}: {content}")

        return "\n\n".join(context_parts)

    def _validate_response_completeness(self, response_text: str, query: str) -> Dict:
        """Validate that the response is complete and precise"""
        validation_issues = []

        # Check if response appears truncated
        if response_text.endswith('...') or len(response_text) < 200:
            validation_issues.append("Response appears truncated or too short")

        # Check for incomplete sentences (but allow single words like "High", "Medium", "Low")
        response_end = response_text.strip()
        if (not response_end.endswith(('.', '!', '?', ':')) and
            len(response_end.split()[-1]) > 15):  # Only flag if last word is very long (likely truncated)
            validation_issues.append("Response ends mid-sentence")

        # Check for specific information requirements
        info_keywords = ['information', 'required', 'need', 'provide', 'documents', 'forms']
        if any(keyword in query.lower() for keyword in info_keywords):
            if not any(keyword in response_text.lower() for keyword in ['annual', 'monthly', 'registration', 'certificate', 'return', 'form', 'report']):
                validation_issues.append("Missing specific information requirements")

        # Check for numbered lists when appropriate
        if 'what information' in query.lower() or 'what do' in query.lower():
            if not any(char in response_text for char in ['1.', '2.', '•', '-']):
                validation_issues.append("Missing structured list format")

        return {
            'is_complete': len(validation_issues) == 0,
            'issues': validation_issues,
            'needs_retry': len(validation_issues) > 0
        }

    def _regenerate_with_validation(self, query: str, context_text: str, classification_result=None, interpretation_result=None, max_retries: int = 2) -> str:
        """Generate response with validation and retry logic"""
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"Generating response attempt {attempt + 1}/{max_retries + 1}")

                # Generate response
                llm_response = self._generate_llm_response(query, context_text, classification_result, interpretation_result)

                # DEBUG: Log raw response details
                logger.info(f"RAW RESPONSE ATTEMPT {attempt + 1}: Length={len(llm_response)}, Ends with: '{llm_response[-50:] if len(llm_response) > 50 else llm_response}'")

                # Validate completeness
                validation = self._validate_response_completeness(llm_response, query)

                if validation['is_complete']:
                    logger.info(f"Response validation passed on attempt {attempt + 1}")
                    return llm_response
                else:
                    logger.warning(f"Response validation failed on attempt {attempt + 1}: {validation['issues']}")

                    # If not the last attempt, modify the prompt for better results
                    if attempt < max_retries:
                        # Add validation instructions to the context
                        enhanced_prompt = f"""VALIDATION REQUIREMENTS - Previous response had these issues: {', '.join(validation['issues'])}

CRITICAL: Ensure your response is:
1. COMPLETE - Do not truncate or cut off mid-sentence
2. SPECIFIC - Include exact documents, forms, values, and data points
3. STRUCTURED - Use numbered lists for information requirements
4. COMPREHENSIVE - Address all aspects of the query

Original Query: {query}

{context_text}

Provide a complete, untruncated response that fully addresses the query."""

                        # Increase token limit for retry
                        temp_max_tokens = min(self.max_response_tokens * 1.5, 8000)

                        response = self.openai_client.chat.completions.create(
                            model=self.llm_model,
                            messages=[
                                {"role": "system", "content": self.system_prompt + "\n\nIMPORTANT: Generate complete, untruncated responses. Never cut off mid-sentence."},
                                {"role": "user", "content": enhanced_prompt}
                            ],
                            max_tokens=int(temp_max_tokens),
                            temperature=self.temperature,
                            seed=42
                        )
                        llm_response = response.choices[0].message.content
                        continue

            except Exception as e:
                logger.error(f"Error in response generation attempt {attempt + 1}: {e}")
                if attempt == max_retries:
                    raise

        # Return the last attempt even if validation failed
        logger.warning("Returning response despite validation issues after max retries")
        return llm_response

    def _log_token_usage(self, query: str, input_tokens: int, output_tokens: int, cost: float):
        """Log token usage for monitoring (Phase 1 basic implementation)"""
        logger.info(f"Token usage - Query: '{query[:50]}...', Input: {input_tokens}, Output: {output_tokens}, Cost: ${cost:.4f}")


def main():
    """Test the Local Primary Response Agent"""
    agent = LocalPrimaryResponseAgent()

    # Test queries
    test_queries = [
        "What is the current payroll tax rate?",
        "How do I calculate stamp duty?",
        "What are the land tax exemptions?"
    ]

    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")

        try:
            # Simulate local vector store documents
            mock_docs = [
                {
                    'act_name': 'payroll_tax_act_2007',
                    'section_number': 'Section 15',
                    'content': 'The rate of payroll tax is 5.45%.',
                    'similarity_score': 0.85
                }
            ]

            response = agent.generate_response(query, mock_docs)

            print(f"📂 Type: {response.query_type}")
            print(f"📊 Confidence: {response.confidence:.2f}")
            print(f"⏱️ Processing time: {response.processing_time:.2f}s")
            print(f"📚 Citations: {len(response.citations)}")

            print(f"\n💬 Answer:")
            print(response.answer)

            if response.citations:
                print(f"\n📖 Citations:")
                for citation in response.citations:
                    print(f"  - {citation}")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()