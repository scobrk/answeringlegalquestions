"""
Enhanced Retrieval Agent for NSW Revenue
Integrates enhanced vector store, relationship engine, and rate calculation service
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import logging
import re
from decimal import Decimal

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from enhanced_vector_store import EnhancedVectorStore
from data.relationship_engine import RelationshipEngine
from data.rate_calculation_service import RateCalculationService

logger = logging.getLogger(__name__)

@dataclass
class EnhancedRetrievalResult:
    """Enhanced retrieval result with comprehensive tax analysis"""
    primary_documents: List[Dict]
    related_tax_analysis: Dict
    rate_calculations: Optional[Dict]
    cross_references: List[str]
    recommendations: List[str]
    warnings: List[str]
    confidence_score: float
    processing_metadata: Dict

class EnhancedRetrievalAgent:
    """
    Enhanced retrieval agent that provides comprehensive NSW Revenue assistance
    """

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)

        # Initialize enhanced components
        self.vector_store = EnhancedVectorStore(data_dir=data_dir)
        self.relationship_engine = RelationshipEngine(metadata_dir=str(self.data_dir / "metadata"))
        self.rate_calculator = RateCalculationService(metadata_dir=str(self.data_dir / "metadata"))

        logger.info("✅ Enhanced Retrieval Agent initialized with all components")

    def enhanced_search(self,
                       query: str,
                       include_calculations: bool = True,
                       include_related_taxes: bool = True,
                       scenario_context: Optional[Dict[str, Any]] = None) -> EnhancedRetrievalResult:
        """
        Perform enhanced search with comprehensive tax analysis

        Args:
            query: User's query
            include_calculations: Whether to include rate calculations
            include_related_taxes: Whether to analyze related taxes
            scenario_context: Additional context for calculations

        Returns:
            EnhancedRetrievalResult with comprehensive analysis
        """
        start_time = datetime.now()

        try:
            # Step 1: Extract tax types and amounts from query
            extracted_info = self._extract_tax_info_from_query(query, scenario_context)

            # Step 2: Perform vector search
            primary_documents = self.vector_store.search_enhanced(
                query=query,
                k=5,
                include_related=include_related_taxes
            )

            # Step 3: Analyze related taxes if requested
            related_tax_analysis = {}
            if include_related_taxes and extracted_info.get('primary_tax'):
                cross_ref_result = self.relationship_engine.analyze_cross_references(
                    primary_tax=extracted_info['primary_tax'],
                    scenario_context=scenario_context
                )
                related_tax_analysis = {
                    'related_taxes': cross_ref_result.related_taxes,
                    'interaction_warnings': cross_ref_result.interaction_warnings,
                    'recommendations': cross_ref_result.recommendations,
                    'confidence': cross_ref_result.confidence_score
                }

            # Step 4: Perform rate calculations if requested and possible
            rate_calculations = None
            if include_calculations and extracted_info.get('calculation_context'):
                rate_calculations = self._perform_rate_calculations(
                    extracted_info['calculation_context'],
                    scenario_context
                )

            # Step 5: Generate cross-references
            cross_references = self._generate_cross_references(primary_documents, related_tax_analysis)

            # Step 6: Compile recommendations and warnings
            recommendations, warnings = self._compile_recommendations_and_warnings(
                primary_documents,
                related_tax_analysis,
                rate_calculations,
                extracted_info
            )

            # Step 7: Calculate overall confidence
            confidence_score = self._calculate_overall_confidence(
                primary_documents,
                related_tax_analysis,
                rate_calculations
            )

            # Step 8: Compile processing metadata
            processing_time = (datetime.now() - start_time).total_seconds()
            processing_metadata = {
                'processing_time_seconds': processing_time,
                'components_used': self._get_components_used(
                    include_calculations, include_related_taxes
                ),
                'extracted_tax_types': extracted_info.get('tax_types', []),
                'calculation_performed': rate_calculations is not None,
                'related_analysis_performed': bool(related_tax_analysis)
            }

            return EnhancedRetrievalResult(
                primary_documents=primary_documents,
                related_tax_analysis=related_tax_analysis,
                rate_calculations=rate_calculations,
                cross_references=cross_references,
                recommendations=recommendations,
                warnings=warnings,
                confidence_score=confidence_score,
                processing_metadata=processing_metadata
            )

        except Exception as e:
            logger.error(f"Error in enhanced search: {e}")
            return self._create_error_result(query, str(e))

    def _extract_tax_info_from_query(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract tax types and calculation context from query"""
        query_lower = query.lower()
        extracted_info = {
            'tax_types': [],
            'primary_tax': None,
            'calculation_context': None,
            'amounts': []
        }

        # Tax type detection
        tax_patterns = {
            'land_tax': ['land tax', 'land_tax'],
            'payroll_tax': ['payroll tax', 'payroll_tax'],
            'duties': ['stamp duty', 'duties', 'conveyance duty', 'transfer duty'],
            'first_home_buyer_grant': ['first home buyer', 'fhb grant', 'first home owner grant']
        }

        for tax_type, patterns in tax_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                extracted_info['tax_types'].append(tax_type)

        # Set primary tax (first detected)
        if extracted_info['tax_types']:
            extracted_info['primary_tax'] = extracted_info['tax_types'][0]

        # Extract amounts for calculations (order matters - most specific first)
        amount_patterns = [
            r'\$([0-9,]+(?:\.[0-9]{1,2})?)\s*million',  # $1.5 million
            r'([0-9]+(?:\.[0-9]+)?)\s*million',  # 1.5 million
            r'\$([0-9,]+(?:\.[0-9]{1,2})?)',  # $1,000.00
            r'([0-9,]+)\s*(?:dollars?|k)',  # 1000 dollars, 500k
        ]

        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean up the amount string
                    clean_amount = match.replace(',', '')

                    # Check the context around the match to determine multiplier
                    if 'million' in query.lower():
                        clean_amount = str(float(clean_amount) * 1000000)
                    elif 'k' in query.lower():
                        clean_amount = str(float(clean_amount) * 1000)

                    amounts.append(Decimal(clean_amount))
                except (ValueError, TypeError):
                    continue

        extracted_info['amounts'] = amounts

        # Create calculation context if we have amounts and tax type
        if amounts and extracted_info['primary_tax']:
            calculation_context = {
                'tax_type': extracted_info['primary_tax'],
                'amounts': amounts
            }

            # Context-specific extraction
            if 'property' in query_lower or 'land' in query_lower or 'home' in query_lower:
                calculation_context['context_type'] = 'property'
                if amounts:
                    calculation_context['property_value'] = amounts[0]

                # Check for first home buyer indicators
                if any(phrase in query_lower for phrase in ['first home', 'fhb', 'first time buyer']):
                    calculation_context['is_first_home_buyer'] = True

                # Check for PPR indicators
                if any(phrase in query_lower for phrase in ['ppr', 'principal place', 'own home', 'live in']):
                    calculation_context['is_principal_place_of_residence'] = True
                else:
                    calculation_context['is_principal_place_of_residence'] = False

            elif 'payroll' in query_lower or 'employees' in query_lower:
                calculation_context['context_type'] = 'business'
                if amounts:
                    calculation_context['annual_payroll'] = amounts[0]

            extracted_info['calculation_context'] = calculation_context

        return extracted_info

    def _perform_rate_calculations(self,
                                 calculation_context: Dict[str, Any],
                                 scenario_context: Optional[Dict] = None) -> Optional[Dict]:
        """Perform rate calculations based on extracted context"""
        try:
            tax_type = calculation_context.get('tax_type')
            context_type = calculation_context.get('context_type')

            if tax_type == 'land_tax' and context_type == 'property':
                property_value = calculation_context.get('property_value')
                is_ppr = calculation_context.get('is_principal_place_of_residence', False)

                if property_value:
                    result = self.rate_calculator.calculate_land_tax(
                        property_value=property_value,
                        is_principal_place_of_residence=is_ppr
                    )
                    return {
                        'tax_type': 'land_tax',
                        'result': result,
                        'summary': f"Land tax: ${result.total_tax:,.2f}{'(exempt)' if result.total_tax == 0 else ''}"
                    }

            elif tax_type == 'payroll_tax' and context_type == 'business':
                annual_payroll = calculation_context.get('annual_payroll')

                if annual_payroll:
                    result = self.rate_calculator.calculate_payroll_tax(
                        annual_payroll=annual_payroll
                    )
                    return {
                        'tax_type': 'payroll_tax',
                        'result': result,
                        'summary': f"Payroll tax: ${result.total_tax:,.2f}"
                    }

            elif tax_type == 'duties' and context_type == 'property':
                property_value = calculation_context.get('property_value')
                is_fhb = calculation_context.get('is_first_home_buyer', False)

                if property_value:
                    result = self.rate_calculator.calculate_stamp_duty(
                        property_value=property_value,
                        is_first_home_buyer=is_fhb
                    )
                    return {
                        'tax_type': 'stamp_duty',
                        'result': result,
                        'summary': f"Stamp duty: ${result.total_tax:,.2f}"
                    }

        except Exception as e:
            logger.error(f"Error in rate calculation: {e}")

        return None

    def _generate_cross_references(self,
                                 primary_documents: List[Dict],
                                 related_tax_analysis: Dict) -> List[str]:
        """Generate cross-references to related legislation"""
        cross_references = []

        # From primary documents
        for doc in primary_documents:
            if doc.get('metadata', {}).get('document_id'):
                cross_references.append(doc['metadata']['document_id'])

        # From related tax analysis
        related_taxes = related_tax_analysis.get('related_taxes', [])
        for tax in related_taxes:
            cross_references.append(f"See also: {tax}")

        return list(set(cross_references))  # Remove duplicates

    def _compile_recommendations_and_warnings(self,
                                            primary_documents: List[Dict],
                                            related_tax_analysis: Dict,
                                            rate_calculations: Optional[Dict],
                                            extracted_info: Dict) -> tuple[List[str], List[str]]:
        """Compile recommendations and warnings from all sources"""
        recommendations = []
        warnings = []

        # From related tax analysis
        if related_tax_analysis:
            recommendations.extend(related_tax_analysis.get('recommendations', []))
            warnings.extend(related_tax_analysis.get('interaction_warnings', []))

        # From rate calculations
        if rate_calculations and rate_calculations.get('result'):
            result = rate_calculations['result']
            warnings.extend(result.warnings)

            if result.exemptions_applied:
                recommendations.append(f"✅ Exemptions applied: {', '.join(result.exemptions_applied)}")

            if result.additional_charges:
                for charge_type, amount in result.additional_charges.items():
                    warnings.append(f"💰 Additional charge: {charge_type} - ${amount:,.2f}")

        # General recommendations based on query analysis
        if len(extracted_info.get('tax_types', [])) > 1:
            recommendations.append("📊 Multiple taxes detected - consider comprehensive tax planning")

        return recommendations, warnings

    def _calculate_overall_confidence(self,
                                    primary_documents: List[Dict],
                                    related_tax_analysis: Dict,
                                    rate_calculations: Optional[Dict]) -> float:
        """Calculate overall confidence score"""
        base_confidence = 0.5

        # Document retrieval confidence
        if primary_documents:
            doc_scores = [doc.get('similarity_score', 0) for doc in primary_documents]
            avg_doc_score = sum(doc_scores) / len(doc_scores)
            doc_confidence = avg_doc_score * 0.3
        else:
            doc_confidence = 0.0

        # Related tax analysis confidence
        related_confidence = related_tax_analysis.get('confidence', 0.5) * 0.2

        # Rate calculation confidence
        calc_confidence = 0.3 if rate_calculations else 0.1

        total_confidence = base_confidence + doc_confidence + related_confidence + calc_confidence

        return min(total_confidence, 1.0)

    def _get_components_used(self, include_calculations: bool, include_related_taxes: bool) -> List[str]:
        """Get list of components used in the search"""
        components = ['enhanced_vector_store']

        if include_related_taxes:
            components.append('relationship_engine')

        if include_calculations:
            components.append('rate_calculation_service')

        return components

    def _create_error_result(self, query: str, error_msg: str) -> EnhancedRetrievalResult:
        """Create error result"""
        return EnhancedRetrievalResult(
            primary_documents=[],
            related_tax_analysis={},
            rate_calculations=None,
            cross_references=[],
            recommendations=[],
            warnings=[f"Error processing query: {error_msg}"],
            confidence_score=0.0,
            processing_metadata={
                'error': error_msg,
                'query': query,
                'timestamp': datetime.now().isoformat()
            }
        )

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return {
            'vector_store': self.vector_store.get_statistics(),
            'relationship_engine': self.relationship_engine.get_tax_network_analysis(),
            'rate_calculator': {
                'available_tax_types': self.rate_calculator.get_available_tax_types()
            }
        }


def main():
    """Test the enhanced retrieval agent"""
    agent = EnhancedRetrievalAgent()

    # Test queries
    test_queries = [
        "What is the land tax on a $2 million property?",
        "Calculate payroll tax for $1.5 million annual payroll",
        "First home buyer stamp duty on $700,000 property",
        "Land tax exemptions for principal place of residence"
    ]

    print("📊 System Statistics:")
    stats = agent.get_system_statistics()
    for component, data in stats.items():
        print(f"\n{component}:")
        for key, value in data.items():
            print(f"  {key}: {value}")

    print("\n" + "="*80)
    print("🔍 ENHANCED RETRIEVAL TESTS")
    print("="*80)

    for query in test_queries:
        print(f"\n🔎 Query: {query}")
        print("-" * 60)

        result = agent.enhanced_search(
            query=query,
            include_calculations=True,
            include_related_taxes=True
        )

        print(f"📄 Documents found: {len(result.primary_documents)}")
        print(f"🔗 Cross-references: {len(result.cross_references)}")
        print(f"📊 Confidence: {result.confidence_score:.2f}")

        if result.rate_calculations:
            print(f"💰 Calculation: {result.rate_calculations['summary']}")

        if result.related_tax_analysis.get('related_taxes'):
            print(f"🔄 Related taxes: {', '.join(result.related_tax_analysis['related_taxes'])}")

        if result.recommendations:
            print("✅ Recommendations:")
            for rec in result.recommendations[:3]:  # Show top 3
                print(f"  • {rec}")

        if result.warnings:
            print("⚠️  Warnings:")
            for warning in result.warnings[:3]:  # Show top 3
                print(f"  • {warning}")

        print(f"⏱️  Processing time: {result.processing_metadata.get('processing_time_seconds', 0):.2f}s")


if __name__ == "__main__":
    main()