"""
Interpretation Agent for NSW Revenue AI Assistant
Analyzes retrieved sources and flags missing information
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class InterpretationResult:
    """Result of source interpretation"""
    interpretation: str
    confidence: float
    completeness_score: float
    missing_information: List[str]
    source_gaps: List[str]
    reliability_assessment: str
    recommendations: List[str]
    key_findings: List[str]
    contradictions: List[str]
    date_sensitivity: bool
    requires_additional_sources: bool


@dataclass
class SourceAnalysis:
    """Analysis of individual source"""
    source_id: str
    relevance_to_query: float
    information_quality: str
    coverage_areas: List[str]
    missing_areas: List[str]
    reliability_factors: List[str]
    date_concerns: List[str]


class InterpretationAgent:
    """
    Agent that interprets retrieved sources and identifies gaps
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Model settings
        self.model = "gpt-4o-mini"
        self.temperature = 0.1
        self.max_tokens = 2000

        # Comprehensive NSW Revenue context knowledge - all 67 types
        self.nsw_revenue_domains = {
            # Property Related (11 types)
            'transfer_duty': ['rates', 'concessions', 'first_home_buyer', 'exemptions', 'calculation', 'foreign_surcharge', 'premium_duty'],
            'foreign_purchaser_duty': ['8_percent_rate', 'eligibility', 'property_types', 'exemptions', 'declaration'],
            'land_tax': ['rates', 'thresholds', 'exemptions', 'principal_residence', 'premium_rates', 'assessment', 'grouping'],
            'parking_space_levy': ['rates', 'sydney_cbd', 'districts', 'annual_returns', 'liability'],
            'premium_property_tax': ['2_percent_rate', '5_million_threshold', 'calculation', 'assessment'],

            # Business Taxation (8 types)
            'payroll_tax': ['5.45_percent_rate', '1.2_million_threshold', 'grouping', 'contractors', 'exemptions', 'returns'],
            'payroll_tax_rebate': ['rebate_rates', 'incentives', 'eligibility', 'application_process'],
            'small_business_grant': ['grant_amounts', 'eligibility', 'employment_targets', 'application'],
            'contractor_provisions': ['contractor_test', 'payments', 'liability', 'exemptions'],

            # Motor Vehicle (5 types)
            'motor_vehicle_duty': ['rates', 'thresholds', 'electric_exemption', 'luxury_rates', 'calculation'],
            'vehicle_registration': ['annual_fees', 'ctp_components', 'categories', 'concessions'],
            'ctp_insurance_levy': ['maof_levy', 'ltcs_levy', 'maitcb_levy', 'rates'],
            'electric_vehicle_exemption': ['78000_threshold', 'eligibility', 'exemption_period'],

            # Gaming and Liquor (8 types)
            'gaming_machine_tax': ['rates', 'thresholds', 'hotels', 'clubs', 'quarterly_returns'],
            'betting_tax': ['point_of_consumption', 'rates', 'returns', 'liability'],
            'point_of_consumption_tax': ['online_betting', 'rates', 'customer_location'],
            'casino_tax': ['rates', 'revenue_thresholds', 'returns'],
            'liquor_licensing_fees': ['licence_types', 'fees', 'applications', 'renewals'],

            # Mining and Resources (8 types)
            'coal_royalty': ['rates', 'annual_returns', 'quarterly_thresholds', 'calculation'],
            'mineral_royalty': ['fixed_rates', 'ad_valorem', '4_percent', 'exemption_threshold'],
            'petroleum_royalty': ['10_percent_rate', 'wellhead_value', 'onshore_offshore'],
            'gas_royalty': ['rates', 'calculation', 'pipeline_values'],
            'quarrying_royalty': ['rates', 'materials', 'calculation'],

            # Environmental (4 types)
            'waste_levy': ['rates', 'landfill', 'disposal', 'exemptions'],
            'emergency_services_levy': ['property_levy', 'rates', 'exemptions', 'categories'],
            'biodiversity_offset_levy': ['offset_calculations', 'rates', 'applications'],

            # Grants and Schemes (5 types)
            'first_home_owner_grant': ['10000_grant', '750000_threshold', 'new_homes', 'eligibility'],
            'shared_equity_scheme': ['equity_share', 'eligibility', 'repayment'],
            'energy_savings_scheme': ['certificates', 'targets', 'penalties'],

            # Fines and Penalties (4 types)
            'penalty_notices': ['payment_options', '28_days', 'enforcement', 'review_rights'],
            'work_development_orders': ['wdo', 'eligible_persons', 'activities', 'dollar_for_dollar'],
            'penalty_interest': ['rates', 'calculation', 'waiver'],

            # Insurance and Levies (7 types)
            'health_insurance_levy': ['rates', 'categories', 'exemptions'],
            'workers_compensation_levy': ['rates', 'industry_classifications', 'calculation'],
            'insurance_protection_tax': ['rates', 'insurance_types', 'calculation'],

            # Administration (7 types)
            'revenue_administration': ['objections', 'appeals', 'enforcement', 'penalties', 'assessment', 'compliance'],
            'objections_appeals': ['60_day_period', '28_day_appeal', 'grounds', 'process'],
            'unclaimed_money': ['reporting', 'claims', 'search', 'entitlements'],
            'hardship_provisions': ['payment_arrangements', 'deferrals', 'eligibility']
        }

        # Critical information requirements
        self.critical_elements = {
            'rates': ['current_rate', 'effective_date', 'calculation_method'],
            'thresholds': ['amount', 'indexation', 'effective_period'],
            'exemptions': ['eligibility_criteria', 'application_process', 'limitations'],
            'deadlines': ['payment_due', 'lodgement_due', 'appeal_periods'],
            'penalties': ['rate', 'calculation', 'waiver_conditions']
        }

    def interpret_sources(self, query: str, sources, query_context: str = None) -> InterpretationResult:
        """
        Main interpretation method

        Args:
            query: Original user query
            sources: Retrieved source documents
            query_context: Additional context about the query type

        Returns:
            InterpretationResult with comprehensive analysis
        """
        logger.info(f"Interpreting {len(sources)} sources for query: {query}")

        try:
            # Step 1: Analyze individual sources
            source_analyses = self._analyze_individual_sources(query, sources)

            # Step 2: Identify query requirements
            query_requirements = self._identify_query_requirements(query)

            # Step 3: Assess source coverage
            coverage_assessment = self._assess_source_coverage(query_requirements, source_analyses)

            # Step 4: Generate interpretation
            interpretation = self._generate_interpretation(query, sources, coverage_assessment)

            # Step 5: Identify gaps and missing information
            gaps_analysis = self._identify_information_gaps(query_requirements, source_analyses)

            # Step 6: Calculate confidence and completeness
            confidence, completeness = self._calculate_confidence_completeness(
                source_analyses, coverage_assessment, gaps_analysis
            )

            # Step 7: Generate recommendations
            recommendations = self._generate_recommendations(gaps_analysis, source_analyses)

            return InterpretationResult(
                interpretation=interpretation,
                confidence=confidence,
                completeness_score=completeness,
                missing_information=gaps_analysis['missing_info'],
                source_gaps=gaps_analysis['source_gaps'],
                reliability_assessment=coverage_assessment['reliability'],
                recommendations=recommendations,
                key_findings=coverage_assessment['key_findings'],
                contradictions=coverage_assessment['contradictions'],
                date_sensitivity=gaps_analysis['date_sensitive'],
                requires_additional_sources=gaps_analysis['needs_more_sources']
            )

        except Exception as e:
            logger.error(f"Error in interpretation: {e}")
            return self._generate_error_result(query, str(e))

    def _analyze_individual_sources(self, query: str, sources) -> List[SourceAnalysis]:
        """Analyze each source individually"""
        analyses = []

        for i, source in enumerate(sources):
            try:
                # Extract source content and metadata - handle both dict and ContextDocument
                if hasattr(source, 'content'):
                    # ContextDocument object
                    content = source.content or ''
                    title = source.title or f'Source {i+1}'
                    source_type = source.source or 'unknown'
                else:
                    # Dictionary object
                    content = source.get('content', '')
                    title = source.get('title', f'Source {i+1}')
                    source_type = source.get('source', 'unknown')

                # Analyze relevance to query
                relevance = self._assess_source_relevance(query, content, title)

                # Assess information quality
                quality = self._assess_information_quality(content, source_type)

                # Identify coverage areas
                coverage_areas = self._identify_coverage_areas(content)

                # Identify missing areas for this query
                missing_areas = self._identify_missing_areas(query, content, coverage_areas)

                # Assess reliability factors
                reliability_factors = self._assess_reliability_factors(content, source_type, title)

                # Check for date-related concerns
                date_concerns = self._check_date_concerns(content)

                analysis = SourceAnalysis(
                    source_id=f"source_{i+1}",
                    relevance_to_query=relevance,
                    information_quality=quality,
                    coverage_areas=coverage_areas,
                    missing_areas=missing_areas,
                    reliability_factors=reliability_factors,
                    date_concerns=date_concerns
                )
                analyses.append(analysis)

            except Exception as e:
                logger.warning(f"Error analyzing source {i+1}: {e}")
                continue

        return analyses

    def _identify_query_requirements(self, query: str) -> Dict:
        """Identify what information the query requires"""
        query_lower = query.lower()
        requirements = {
            'domain': None,
            'info_types': [],
            'specificity': 'general',
            'time_sensitivity': False,
            'calculation_needed': False,
            'procedural_info': False
        }

        # Identify domain
        for domain, keywords in self.nsw_revenue_domains.items():
            domain_terms = domain.replace('_', ' ').split() + keywords
            if any(term in query_lower for term in domain_terms):
                requirements['domain'] = domain
                break

        # Identify information types needed
        if any(word in query_lower for word in ['rate', 'percentage', '%']):
            requirements['info_types'].append('rates')
        if any(word in query_lower for word in ['threshold', 'limit', 'minimum']):
            requirements['info_types'].append('thresholds')
        if any(word in query_lower for word in ['exemption', 'exempt', 'concession']):
            requirements['info_types'].append('exemptions')
        if any(word in query_lower for word in ['calculate', 'calculation', 'how much']):
            requirements['calculation_needed'] = True
        if any(word in query_lower for word in ['apply', 'application', 'process', 'how to']):
            requirements['procedural_info'] = True

        # Check time sensitivity
        if any(word in query_lower for word in ['current', 'latest', '2024', '2025', 'now']):
            requirements['time_sensitivity'] = True

        # Assess specificity
        if any(word in query_lower for word in ['specific', 'exactly', 'precise']) or '$' in query:
            requirements['specificity'] = 'high'
        elif len(query.split()) > 10:
            requirements['specificity'] = 'detailed'

        return requirements

    def _assess_source_coverage(self, requirements: Dict, analyses: List[SourceAnalysis]) -> Dict:
        """Assess how well sources cover the query requirements"""
        coverage = {
            'domain_coverage': 0.0,
            'info_type_coverage': {},
            'overall_coverage': 0.0,
            'reliability': 'medium',
            'key_findings': [],
            'contradictions': []
        }

        if not analyses:
            return coverage

        # Calculate domain coverage
        domain_relevant_sources = [a for a in analyses if a.relevance_to_query > 0.3]
        coverage['domain_coverage'] = len(domain_relevant_sources) / len(analyses)

        # Calculate information type coverage
        for info_type in requirements.get('info_types', []):
            covered_sources = []
            for analysis in analyses:
                if any(info_type in area.lower() for area in analysis.coverage_areas):
                    covered_sources.append(analysis)
            coverage['info_type_coverage'][info_type] = len(covered_sources) / len(analyses)

        # Calculate overall coverage
        if requirements['info_types']:
            type_scores = list(coverage['info_type_coverage'].values())
            coverage['overall_coverage'] = (coverage['domain_coverage'] + sum(type_scores) / len(type_scores)) / 2
        else:
            coverage['overall_coverage'] = coverage['domain_coverage']

        # Assess overall reliability
        high_quality_sources = [a for a in analyses if a.information_quality in ['high', 'excellent']]
        if len(high_quality_sources) >= len(analyses) * 0.6:
            coverage['reliability'] = 'high'
        elif len(high_quality_sources) >= len(analyses) * 0.3:
            coverage['reliability'] = 'medium'
        else:
            coverage['reliability'] = 'low'

        # Extract key findings
        for analysis in analyses:
            if analysis.relevance_to_query > 0.5:
                for area in analysis.coverage_areas:
                    if area not in coverage['key_findings']:
                        coverage['key_findings'].append(area)

        return coverage

    def _generate_interpretation(self, query: str, sources, coverage: Dict) -> str:
        """Generate LLM-based interpretation of sources"""
        try:
            # Prepare source content for LLM
            source_content = ""
            for i, source in enumerate(sources, 1):
                # Handle both dict and ContextDocument
                if hasattr(source, 'content'):
                    content = (source.content or '')[:500]  # Limit content length
                    title = source.title or f'Source {i}'
                else:
                    content = source.get('content', '')[:500]  # Limit content length
                    title = source.get('title', f'Source {i}')
                source_content += f"\n=== Source {i}: {title} ===\n{content}\n"

            # Create interpretation prompt
            prompt = f"""As an expert NSW Revenue legislation interpreter, analyze the following sources to answer this query: "{query}"

SOURCES:
{source_content}

ANALYSIS REQUIREMENTS:
1. Provide a direct, accurate interpretation based solely on the sources
2. Clearly state what information is available vs. missing
3. Flag any ambiguities or contradictions
4. Indicate confidence level in the interpretation
5. Note if sources appear outdated or incomplete
6. **SPECIFY EXACT INFORMATION REQUIREMENTS** - Detail what documents, forms, values, and data points are needed

ENHANCED INTERPRETATION FORMAT:
**Direct Answer:** [Based on available sources]
**Specific Information Required:** [List exact documents, forms, values, and data points needed to comply/calculate/apply]
**Source Analysis:** [What sources say and their reliability]
**Information Gaps:** [What's missing or unclear]
**Confidence Assessment:** [High/Medium/Low and why]

Focus on providing specific, actionable information requirements that reference the exact documentation and data needed."""

            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert NSW Revenue legislation interpreter. Be precise, accurate, highlight gaps, and ALWAYS specify exact information requirements including forms, documents, values, and data points needed for compliance, calculations, or applications."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating interpretation: {e}")
            return f"Unable to generate interpretation due to error: {str(e)}"

    def _identify_information_gaps(self, requirements: Dict, analyses: List[SourceAnalysis]) -> Dict:
        """Identify what information is missing"""
        gaps = {
            'missing_info': [],
            'source_gaps': [],
            'date_sensitive': False,
            'needs_more_sources': False
        }

        # Check for missing information types
        required_info = requirements.get('info_types', [])
        for info_type in required_info:
            covered = False
            for analysis in analyses:
                if any(info_type in area.lower() for area in analysis.coverage_areas):
                    covered = True
                    break
            if not covered:
                gaps['missing_info'].append(f"No sources contain {info_type} information")

        # Check for missing critical elements
        domain = requirements.get('domain')
        if domain and domain in self.critical_elements:
            for element in self.critical_elements[domain]:
                found = False
                for analysis in analyses:
                    if any(element in area.lower() for area in analysis.coverage_areas):
                        found = True
                        break
                if not found:
                    gaps['missing_info'].append(f"Missing {element} information")

        # Check source quality gaps
        low_quality_sources = [a for a in analyses if a.information_quality == 'low']
        if len(low_quality_sources) > len(analyses) * 0.5:
            gaps['source_gaps'].append("Majority of sources have low information quality")

        # Check for source diversity
        source_types = set()
        for analysis in analyses:
            # Extract source type from analysis
            source_types.add("generic")  # Placeholder
        if len(source_types) < 2:
            gaps['source_gaps'].append("Limited source diversity")

        # Check date sensitivity
        if requirements.get('time_sensitivity'):
            date_issues = []
            for analysis in analyses:
                if analysis.date_concerns:
                    date_issues.extend(analysis.date_concerns)
            if date_issues:
                gaps['date_sensitive'] = True
                gaps['missing_info'].append("Current/updated information may be required")

        # Determine if more sources needed
        if len(analyses) < 3 or gaps['missing_info'] or gaps['source_gaps']:
            gaps['needs_more_sources'] = True

        return gaps

    def _calculate_confidence_completeness(self, analyses: List[SourceAnalysis],
                                         coverage: Dict, gaps: Dict) -> Tuple[float, float]:
        """Calculate confidence and completeness scores"""

        # Base confidence from source quality
        if not analyses:
            return 0.0, 0.0

        quality_scores = {'high': 0.9, 'medium': 0.6, 'low': 0.3}
        avg_quality = sum(quality_scores.get(a.information_quality, 0.3) for a in analyses) / len(analyses)

        # Adjust for coverage
        coverage_bonus = coverage['overall_coverage'] * 0.3

        # Penalty for gaps
        gap_penalty = len(gaps['missing_info']) * 0.1

        confidence = max(0.0, min(1.0, avg_quality + coverage_bonus - gap_penalty))

        # Completeness based on coverage and missing information
        completeness = coverage['overall_coverage']
        if gaps['missing_info']:
            completeness *= (1 - len(gaps['missing_info']) * 0.2)

        completeness = max(0.0, min(1.0, completeness))

        return confidence, completeness

    def _generate_recommendations(self, gaps: Dict, analyses: List[SourceAnalysis]) -> List[str]:
        """Generate recommendations for improving information quality"""
        recommendations = []

        if gaps['needs_more_sources']:
            recommendations.append("Retrieve additional sources for more comprehensive coverage")

        if gaps['missing_info']:
            recommendations.append("Seek specific sources addressing: " + ", ".join(gaps['missing_info'][:3]))

        if gaps['date_sensitive']:
            recommendations.append("Verify information currency with latest NSW Revenue publications")

        if gaps['source_gaps']:
            recommendations.append("Improve source quality and diversity")

        # Source-specific recommendations
        low_relevance = [a for a in analyses if a.relevance_to_query < 0.4]
        if len(low_relevance) > len(analyses) * 0.4:
            recommendations.append("Focus search on more directly relevant sources")

        return recommendations

    def _assess_source_relevance(self, query: str, content: str, title: str) -> float:
        """Assess how relevant a source is to the query"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        title_words = set(title.lower().split())

        # Word overlap scoring
        content_overlap = len(query_words.intersection(content_words)) / len(query_words)
        title_overlap = len(query_words.intersection(title_words)) / len(query_words)

        # Weighted relevance
        relevance = (content_overlap * 0.7) + (title_overlap * 0.3)

        return min(1.0, relevance)

    def _assess_information_quality(self, content: str, source_type: str) -> str:
        """Assess the quality of information in a source"""

        # Length-based assessment
        if len(content) < 100:
            return 'low'

        # Source type bonus
        quality_score = 0.5
        if source_type in ['nsw_revenue_web', 'official']:
            quality_score += 0.3
        elif source_type in ['huggingface', 'legal_corpus']:
            quality_score += 0.2

        # Content quality indicators
        if any(indicator in content.lower() for indicator in ['section', 'act', 'regulation']):
            quality_score += 0.2

        if any(indicator in content.lower() for indicator in ['rate', 'amount', 'threshold']):
            quality_score += 0.1

        if quality_score >= 0.8:
            return 'high'
        elif quality_score >= 0.6:
            return 'medium'
        else:
            return 'low'

    def _identify_coverage_areas(self, content: str) -> List[str]:
        """Identify what areas of information the source covers"""
        areas = []
        content_lower = content.lower()

        # Map content to coverage areas
        coverage_mapping = {
            'rates': ['rate', 'percentage', '%', 'tax rate'],
            'thresholds': ['threshold', 'limit', 'minimum', 'maximum'],
            'exemptions': ['exempt', 'exemption', 'concession', 'relief'],
            'calculation': ['calculate', 'formula', 'computation'],
            'procedures': ['apply', 'application', 'process', 'steps'],
            'penalties': ['penalty', 'fine', 'interest', 'late payment'],
            'appeals': ['appeal', 'objection', 'review', 'dispute']
        }

        for area, keywords in coverage_mapping.items():
            if any(keyword in content_lower for keyword in keywords):
                areas.append(area)

        return areas

    def _identify_missing_areas(self, query: str, content: str, coverage_areas: List[str]) -> List[str]:
        """Identify what areas are missing for the specific query"""
        query_requirements = self._identify_query_requirements(query)
        required_info = query_requirements.get('info_types', [])

        missing = []
        for req in required_info:
            if req not in coverage_areas:
                missing.append(req)

        return missing

    def _assess_reliability_factors(self, content: str, source_type: str, title: str) -> List[str]:
        """Assess factors affecting source reliability"""
        factors = []

        # Source type reliability
        if source_type == 'nsw_revenue_web':
            factors.append("Official NSW Revenue source")
        elif source_type == 'huggingface':
            factors.append("Third-party legal corpus")
        elif source_type == 'local':
            factors.append("Cached/local content")

        # Content reliability indicators
        if any(term in content.lower() for term in ['current', 'effective', '2024', '2025']):
            factors.append("Contains current date references")

        if any(term in content.lower() for term in ['section', 'subsection', 'act']):
            factors.append("Contains specific legal references")

        return factors

    def _check_date_concerns(self, content: str) -> List[str]:
        """Check for date-related concerns in the source"""
        concerns = []
        content_lower = content.lower()

        # Look for old dates
        old_years = ['2020', '2021', '2022', '2023']
        for year in old_years:
            if year in content and '2024' not in content and '2025' not in content:
                concerns.append(f"Content may contain outdated information from {year}")

        # Look for date sensitivity indicators
        if any(term in content_lower for term in ['rate', 'threshold', 'amount']):
            if not any(term in content_lower for term in ['current', 'effective', '2024', '2025']):
                concerns.append("Rates/amounts shown may not be current")

        return concerns

    def _generate_error_result(self, query: str, error_msg: str) -> InterpretationResult:
        """Generate error result when interpretation fails"""
        return InterpretationResult(
            interpretation=f"Error interpreting sources for query '{query}': {error_msg}",
            confidence=0.0,
            completeness_score=0.0,
            missing_information=["Unable to analyze sources due to error"],
            source_gaps=["Source analysis failed"],
            reliability_assessment="unknown",
            recommendations=["Retry source interpretation"],
            key_findings=[],
            contradictions=[],
            date_sensitivity=False,
            requires_additional_sources=True
        )


def main():
    """Test the interpretation agent"""
    agent = InterpretationAgent()

    # Test sources
    test_sources = [
        {
            'title': 'Payroll Tax Act 2007 (NSW)',
            'content': 'The rate of payroll tax is 5.45%. The tax-free threshold is $1,200,000 per financial year.',
            'source': 'nsw_revenue_web',
            'relevance_score': 0.85
        },
        {
            'title': 'Land Tax Information',
            'content': 'Land tax rates vary based on property value. Exemptions available for principal residence.',
            'source': 'local',
            'relevance_score': 0.3
        }
    ]

    test_queries = [
        "What is the current payroll tax rate in NSW?",
        "How do I calculate land tax for a $2 million property?",
        "What are the penalty rates for late payroll tax payments?"
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print('='*60)

        result = agent.interpret_sources(query, test_sources)

        print(f"Confidence: {result.confidence:.2f}")
        print(f"Completeness: {result.completeness_score:.2f}")
        print(f"Requires additional sources: {result.requires_additional_sources}")

        print(f"\nInterpretation:\n{result.interpretation}")

        if result.missing_information:
            print(f"\nMissing Information:")
            for item in result.missing_information:
                print(f"  - {item}")

        if result.recommendations:
            print(f"\nRecommendations:")
            for rec in result.recommendations:
                print(f"  - {rec}")


if __name__ == "__main__":
    main()