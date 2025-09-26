"""
Relationship Engine for NSW Revenue Cross-References
Manages tax relationships and cross-reference analysis using NetworkX
"""

import json
import networkx as nx
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TaxRelationship:
    """Represents a relationship between two tax types"""
    primary_tax: str
    secondary_tax: str
    relationship_type: str  # complementary, conflicting, prerequisite, alternative
    strength: float  # 0.0 to 1.0
    context: str
    interaction_rules: Dict[str, Any]
    bidirectional: bool = True

@dataclass
class CrossReferenceResult:
    """Result of cross-reference analysis"""
    related_taxes: List[str]
    relationship_paths: List[List[str]]
    interaction_warnings: List[str]
    recommendations: List[str]
    confidence_score: float

class RelationshipEngine:
    """
    Advanced relationship engine for NSW Revenue tax cross-references
    """

    def __init__(self, metadata_dir: str = "./data/metadata"):
        self.metadata_dir = Path(metadata_dir)
        self.relationship_graph = nx.Graph()
        self.tax_properties = {}  # Tax-specific properties and rules

        # Relationship type weights for scoring
        self.relationship_weights = {
            'complementary': 0.9,
            'prerequisite': 0.8,
            'alternative': 0.7,
            'conflicting': 0.5,
            'beneficial': 0.8,
            'temporal': 0.6
        }

        # Load relationship data
        self._load_relationships()
        self._load_tax_properties()

    def _load_relationships(self) -> None:
        """Load tax relationship mappings"""
        relationships_file = self.metadata_dir / "relationships.json"

        if not relationships_file.exists():
            logger.warning("No relationships file found")
            return

        try:
            with open(relationships_file, 'r') as f:
                data = json.load(f)

            relationships = data.get('relationships', [])

            for rel in relationships:
                primary_tax = rel.get('primary_tax')
                secondary_tax = rel.get('secondary_tax')
                relationship_type = rel.get('relationship_type')
                interaction_rules = rel.get('interaction_rules', {})

                if primary_tax and secondary_tax:
                    # Add nodes with tax properties
                    for tax in [primary_tax, secondary_tax]:
                        if not self.relationship_graph.has_node(tax):
                            self.relationship_graph.add_node(
                                tax,
                                type='tax',
                                category=self._infer_category(tax),
                                active=True
                            )

                    # Add edge with relationship metadata
                    weight = self.relationship_weights.get(relationship_type, 0.5)

                    self.relationship_graph.add_edge(
                        primary_tax,
                        secondary_tax,
                        relationship_type=relationship_type,
                        weight=weight,
                        interaction_rules=interaction_rules,
                        bidirectional=True
                    )

            logger.info(f"✅ Loaded {len(relationships)} relationships into graph")

        except Exception as e:
            logger.error(f"Error loading relationships: {e}")

    def _load_tax_properties(self) -> None:
        """Load tax-specific properties and calculation rules"""
        # This would load detailed tax properties from metadata files
        # For now, we'll use basic properties based on tax names

        self.tax_properties = {
            'land_tax': {
                'tax_base': 'property_value',
                'collection_frequency': 'annual',
                'applies_to': ['property_owners'],
                'exemptions': ['principal_place_of_residence', 'primary_production'],
                'calculation_basis': 'progressive_rates',
                'timing': 'annual_assessment'
            },
            'duties': {
                'tax_base': 'transaction_value',
                'collection_frequency': 'transaction_based',
                'applies_to': ['property_purchasers'],
                'exemptions': ['first_home_buyer', 'intergenerational_transfer'],
                'calculation_basis': 'progressive_rates',
                'timing': 'at_settlement'
            },
            'payroll_tax': {
                'tax_base': 'wages_paid',
                'collection_frequency': 'monthly',
                'applies_to': ['employers'],
                'exemptions': ['small_business_threshold'],
                'calculation_basis': 'flat_rate_above_threshold',
                'timing': 'monthly_returns'
            },
            'first_home_buyer_grant': {
                'tax_base': 'not_applicable',
                'collection_frequency': 'application_based',
                'applies_to': ['first_home_buyers'],
                'exemptions': [],
                'calculation_basis': 'fixed_amount',
                'timing': 'at_settlement'
            }
        }

    def _infer_category(self, tax_name: str) -> str:
        """Infer tax category from tax name"""
        if 'land' in tax_name.lower():
            return 'property_taxes'
        elif 'duty' in tax_name.lower() or 'duties' in tax_name.lower():
            return 'property_taxes'
        elif 'payroll' in tax_name.lower():
            return 'business_taxes'
        elif 'grant' in tax_name.lower():
            return 'grants_and_schemes'
        else:
            return 'other'

    def analyze_cross_references(self,
                                primary_tax: str,
                                scenario_context: Dict[str, Any] = None) -> CrossReferenceResult:
        """
        Analyze cross-references for a given tax and scenario

        Args:
            primary_tax: The main tax being analyzed
            scenario_context: Context about the scenario (e.g., property_value, business_type)

        Returns:
            CrossReferenceResult with related taxes and interactions
        """

        if primary_tax not in self.relationship_graph:
            return CrossReferenceResult(
                related_taxes=[],
                relationship_paths=[],
                interaction_warnings=[f"No relationships found for {primary_tax}"],
                recommendations=[],
                confidence_score=0.0
            )

        # Find directly related taxes
        direct_neighbors = list(self.relationship_graph.neighbors(primary_tax))

        # Find taxes within 2 degrees of separation
        related_taxes = set(direct_neighbors)
        for neighbor in direct_neighbors:
            second_degree = list(self.relationship_graph.neighbors(neighbor))
            related_taxes.update(second_degree)

        # Remove the primary tax itself
        related_taxes.discard(primary_tax)
        related_taxes = list(related_taxes)

        # Generate relationship paths
        relationship_paths = []
        for related_tax in related_taxes:
            try:
                if related_tax in direct_neighbors:
                    # Direct relationship
                    relationship_paths.append([primary_tax, related_tax])
                else:
                    # Find shortest path
                    path = nx.shortest_path(self.relationship_graph, primary_tax, related_tax)
                    if len(path) <= 3:  # Only include short paths
                        relationship_paths.append(path)
            except nx.NetworkXNoPath:
                continue

        # Analyze interactions and generate warnings
        interaction_warnings = self._analyze_interactions(primary_tax, related_taxes, scenario_context)

        # Generate recommendations
        recommendations = self._generate_recommendations(primary_tax, related_taxes, scenario_context)

        # Calculate confidence score
        confidence_score = self._calculate_confidence(primary_tax, related_taxes, scenario_context)

        return CrossReferenceResult(
            related_taxes=related_taxes,
            relationship_paths=relationship_paths,
            interaction_warnings=interaction_warnings,
            recommendations=recommendations,
            confidence_score=confidence_score
        )

    def _analyze_interactions(self,
                            primary_tax: str,
                            related_taxes: List[str],
                            scenario_context: Dict[str, Any] = None) -> List[str]:
        """Analyze potential interactions and conflicts"""
        warnings = []

        for related_tax in related_taxes:
            if self.relationship_graph.has_edge(primary_tax, related_tax):
                edge_data = self.relationship_graph.get_edge_data(primary_tax, related_tax)
                relationship_type = edge_data.get('relationship_type')
                interaction_rules = edge_data.get('interaction_rules', {})

                if relationship_type == 'conflicting':
                    warnings.append(f"⚠️  {related_tax} may conflict with {primary_tax}")

                elif relationship_type == 'prerequisite':
                    warnings.append(f"📋 {related_tax} is required before {primary_tax} applies")

                elif relationship_type == 'complementary':
                    warnings.append(f"💡 {related_tax} may also apply alongside {primary_tax}")

                # Context-specific warnings
                if scenario_context:
                    warnings.extend(self._analyze_context_specific_interactions(
                        primary_tax, related_tax, scenario_context, interaction_rules
                    ))

        return warnings

    def _analyze_context_specific_interactions(self,
                                             primary_tax: str,
                                             related_tax: str,
                                             scenario_context: Dict[str, Any],
                                             interaction_rules: Dict[str, Any]) -> List[str]:
        """Analyze interactions based on specific scenario context"""
        warnings = []

        # Property transaction scenarios
        if scenario_context.get('transaction_type') == 'property_purchase':
            if primary_tax == 'duties' and related_tax == 'land_tax':
                warnings.append("🏠 Land tax will apply annually after property purchase")

            if 'first_home_buyer' in scenario_context.get('buyer_type', ''):
                if related_tax == 'first_home_buyer_grant':
                    warnings.append("💰 First home buyer benefits may be available")

        # Business scenarios
        if scenario_context.get('entity_type') == 'business':
            if primary_tax == 'payroll_tax':
                payroll_amount = scenario_context.get('annual_payroll', 0)
                if payroll_amount > 1300000:  # NSW threshold
                    warnings.append(f"💼 Payroll tax applies: annual payroll ${payroll_amount:,} exceeds threshold")

        return warnings

    def _generate_recommendations(self,
                                primary_tax: str,
                                related_taxes: List[str],
                                scenario_context: Dict[str, Any] = None) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Basic recommendations based on relationships
        for related_tax in related_taxes:
            if self.relationship_graph.has_edge(primary_tax, related_tax):
                edge_data = self.relationship_graph.get_edge_data(primary_tax, related_tax)
                relationship_type = edge_data.get('relationship_type')

                if relationship_type == 'beneficial':
                    recommendations.append(f"✅ Consider {related_tax} for potential benefits")

                elif relationship_type == 'alternative':
                    recommendations.append(f"🔄 {related_tax} may be an alternative to {primary_tax}")

        # Context-specific recommendations
        if scenario_context:
            recommendations.extend(self._generate_context_recommendations(
                primary_tax, related_taxes, scenario_context
            ))

        # General recommendations
        if len(related_taxes) > 2:
            recommendations.append("📊 Consider comprehensive tax planning given multiple tax implications")

        return recommendations

    def _generate_context_recommendations(self,
                                        primary_tax: str,
                                        related_taxes: List[str],
                                        scenario_context: Dict[str, Any]) -> List[str]:
        """Generate context-specific recommendations"""
        recommendations = []

        # Property recommendations
        if scenario_context.get('transaction_type') == 'property_purchase':
            property_value = scenario_context.get('property_value', 0)

            if property_value > 3000000 and 'land_tax' in related_taxes:
                recommendations.append("⚡ Premium property tax (2% surcharge) may apply to properties over $3M")

            if scenario_context.get('buyer_type') == 'first_home_buyer':
                recommendations.append("🏡 Explore first home buyer exemptions and grants")

        # Business recommendations
        if scenario_context.get('entity_type') == 'business':
            recommendations.append("📈 Consider payroll tax planning if expanding workforce")

        return recommendations

    def _calculate_confidence(self,
                            primary_tax: str,
                            related_taxes: List[str],
                            scenario_context: Dict[str, Any] = None) -> float:
        """Calculate confidence score for the analysis"""
        base_confidence = 0.7

        # Increase confidence based on number of known relationships
        relationship_bonus = min(len(related_taxes) * 0.05, 0.2)

        # Increase confidence if we have context
        context_bonus = 0.1 if scenario_context else 0.0

        # Increase confidence if primary tax is well-known
        known_tax_bonus = 0.1 if primary_tax in self.tax_properties else 0.0

        confidence = base_confidence + relationship_bonus + context_bonus + known_tax_bonus

        return min(confidence, 1.0)

    def get_tax_network_analysis(self) -> Dict[str, Any]:
        """Get network analysis of the tax relationship graph"""
        return {
            'total_taxes': self.relationship_graph.number_of_nodes(),
            'total_relationships': self.relationship_graph.number_of_edges(),
            'most_connected_taxes': self._get_most_connected_taxes(),
            'relationship_types': self._get_relationship_type_distribution(),
            'network_density': nx.density(self.relationship_graph),
            'connected_components': len(list(nx.connected_components(self.relationship_graph)))
        }

    def _get_most_connected_taxes(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Get the most connected taxes in the network"""
        degree_centrality = nx.degree_centrality(self.relationship_graph)
        sorted_taxes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)
        return [(tax, round(centrality * len(self.relationship_graph.nodes()), 2))
                for tax, centrality in sorted_taxes[:top_n]]

    def _get_relationship_type_distribution(self) -> Dict[str, int]:
        """Get distribution of relationship types"""
        distribution = {}
        for _, _, edge_data in self.relationship_graph.edges(data=True):
            rel_type = edge_data.get('relationship_type', 'unknown')
            distribution[rel_type] = distribution.get(rel_type, 0) + 1
        return distribution

    def find_tax_clusters(self) -> List[List[str]]:
        """Find clusters of related taxes"""
        if self.relationship_graph.number_of_nodes() == 0:
            return []

        # Use connected components to find clusters
        clusters = list(nx.connected_components(self.relationship_graph))
        return [list(cluster) for cluster in clusters if len(cluster) > 1]

    def get_shortest_relationship_path(self, tax1: str, tax2: str) -> Optional[List[str]]:
        """Find shortest relationship path between two taxes"""
        try:
            return nx.shortest_path(self.relationship_graph, tax1, tax2)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def add_relationship(self, tax_relationship: TaxRelationship) -> None:
        """Add a new tax relationship to the graph"""
        # Add nodes if they don't exist
        for tax in [tax_relationship.primary_tax, tax_relationship.secondary_tax]:
            if not self.relationship_graph.has_node(tax):
                self.relationship_graph.add_node(
                    tax,
                    type='tax',
                    category=self._infer_category(tax)
                )

        # Add edge
        self.relationship_graph.add_edge(
            tax_relationship.primary_tax,
            tax_relationship.secondary_tax,
            relationship_type=tax_relationship.relationship_type,
            weight=tax_relationship.strength,
            context=tax_relationship.context,
            interaction_rules=tax_relationship.interaction_rules,
            bidirectional=tax_relationship.bidirectional
        )

        logger.info(f"Added relationship: {tax_relationship.primary_tax} -> {tax_relationship.secondary_tax}")


def main():
    """Test the relationship engine"""
    engine = RelationshipEngine()

    # Test network analysis
    network_stats = engine.get_tax_network_analysis()
    print("📊 Tax Network Analysis:")
    for key, value in network_stats.items():
        print(f"  {key}: {value}")

    # Test cross-reference analysis
    test_scenarios = [
        {
            'tax': 'land_tax',
            'context': {
                'transaction_type': 'property_purchase',
                'property_value': 2000000,
                'buyer_type': 'individual'
            }
        },
        {
            'tax': 'duties',
            'context': {
                'transaction_type': 'property_purchase',
                'property_value': 800000,
                'buyer_type': 'first_home_buyer'
            }
        }
    ]

    for scenario in test_scenarios:
        print(f"\n🔍 Cross-reference analysis for {scenario['tax']}:")
        result = engine.analyze_cross_references(scenario['tax'], scenario['context'])

        print(f"Related taxes: {result.related_taxes}")
        print(f"Confidence: {result.confidence_score:.2f}")

        if result.interaction_warnings:
            print("Warnings:")
            for warning in result.interaction_warnings:
                print(f"  {warning}")

        if result.recommendations:
            print("Recommendations:")
            for rec in result.recommendations:
                print(f"  {rec}")


if __name__ == "__main__":
    main()