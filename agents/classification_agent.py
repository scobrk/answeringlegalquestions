"""
Classification Agent for NSW Revenue AI Assistant
Classifies questions by revenue type and determines intent
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RevenueType(Enum):
    """Comprehensive NSW Revenue types - 67 types"""
    # Property Related (11 types)
    TRANSFER_DUTY = "transfer_duty"  # Stamp Duty
    FOREIGN_PURCHASER_DUTY = "foreign_purchaser_duty"
    LAND_TAX = "land_tax"
    LAND_TAX_MANAGEMENT = "land_tax_management"
    PROPERTY_TAX_FHB = "property_tax_fhb"  # First Home Buyer Choice
    PARKING_SPACE_LEVY = "parking_space_levy"
    PREMIUM_PROPERTY_TAX = "premium_property_tax"  # Properties over $5M
    VACANT_LAND_TAX = "vacant_land_tax"
    FOREIGN_OWNER_SURCHARGE = "foreign_owner_surcharge"
    BUILD_TO_RENT_CONCESSION = "build_to_rent_concession"
    AFFORDABLE_HOUSING_LEVY = "affordable_housing_levy"

    # Business Taxation (8 types)
    PAYROLL_TAX = "payroll_tax"
    PAYROLL_TAX_REBATE = "payroll_tax_rebate"
    SMALL_BUSINESS_GRANT = "small_business_grant"
    REGIONAL_RELOCATION_GRANT = "regional_relocation_grant"
    EMPLOYMENT_INCENTIVE = "employment_incentive"
    SKILLS_INCENTIVE = "skills_incentive"
    CONTRACTOR_PROVISIONS = "contractor_provisions"
    GROUPING_PROVISIONS = "grouping_provisions"

    # Motor Vehicle (5 types)
    MOTOR_VEHICLE_DUTY = "motor_vehicle_duty"
    VEHICLE_REGISTRATION = "vehicle_registration"
    CTP_INSURANCE_LEVY = "ctp_insurance_levy"
    ELECTRIC_VEHICLE_EXEMPTION = "electric_vehicle_exemption"
    LUXURY_VEHICLE_DUTY = "luxury_vehicle_duty"

    # Gaming and Liquor (8 types)
    GAMING_MACHINE_TAX = "gaming_machine_tax"
    BETTING_TAX = "betting_tax"
    POINT_OF_CONSUMPTION_TAX = "point_of_consumption_tax"
    GAMING_WAGERING_TAX = "gaming_wagering_tax"
    LIQUOR_LICENSING_FEES = "liquor_licensing_fees"
    GAMING_LICENCE_FEES = "gaming_licence_fees"
    CASINO_TAX = "casino_tax"
    LOTTERIES_TAX = "lotteries_tax"

    # Royalties (8 types)
    COAL_ROYALTY = "coal_royalty"
    MINERAL_ROYALTY = "mineral_royalty"
    PETROLEUM_ROYALTY = "petroleum_royalty"
    PETROLEUM_OFFSHORE_ROYALTY = "petroleum_offshore_royalty"
    OFFSHORE_MINERALS_ROYALTY = "offshore_minerals_royalty"
    CRITICAL_MINERALS_DEFERRAL = "critical_minerals_deferral"
    GAS_ROYALTY = "gas_royalty"
    QUARRYING_ROYALTY = "quarrying_royalty"

    # Fines and Penalties (4 types)
    PENALTY_NOTICES = "penalty_notices"
    WORK_DEVELOPMENT_ORDERS = "work_development_orders"
    PENALTY_INTEREST = "penalty_interest"
    ENFORCEMENT_COSTS = "enforcement_costs"

    # Insurance and Levies (7 types)
    INSURANCE_PROTECTION_TAX = "insurance_protection_tax"
    HEALTH_INSURANCE_LEVY = "health_insurance_levy"
    EMERGENCY_SERVICES_LEVY = "emergency_services_levy"
    PASSENGER_SERVICE_LEVY = "passenger_service_levy"
    WORKERS_COMPENSATION_LEVY = "workers_compensation_levy"
    PUBLIC_LIABILITY_INSURANCE_LEVY = "public_liability_insurance_levy"
    BUILDING_INSURANCE_LEVY = "building_insurance_levy"

    # Grants and Schemes (5 types)
    FIRST_HOME_OWNER_GRANT = "first_home_owner_grant"
    SHARED_EQUITY_SCHEME = "shared_equity_scheme"
    ENERGY_SAVINGS_SCHEME = "energy_savings_scheme"
    CLIMATE_CHANGE_FUND = "climate_change_fund"
    GROWTH_INFRASTRUCTURE_COMPACT = "growth_infrastructure_compact"

    # Environmental (4 types)
    WASTE_LEVY = "waste_levy"
    ABORIGINAL_LAND_RIGHTS_LEVY = "aboriginal_land_rights_levy"
    ENVIRONMENTAL_PLANNING_LEVY = "environmental_planning_levy"
    BIODIVERSITY_OFFSET_LEVY = "biodiversity_offset_levy"

    # Administration (7 types)
    REVENUE_ADMINISTRATION = "revenue_administration"
    COMMONWEALTH_PLACES_MIRROR = "commonwealth_places_mirror"
    UNCLAIMED_MONEY = "unclaimed_money"
    HARDSHIP_PROVISIONS = "hardship_provisions"
    OBJECTIONS_APPEALS = "objections_appeals"
    TAX_AVOIDANCE_PROVISIONS = "tax_avoidance_provisions"
    RECORD_KEEPING_REQUIREMENTS = "record_keeping_requirements"

    UNKNOWN = "unknown"


class QuestionIntent(Enum):
    """Question intent types"""
    CALCULATION = "calculation"  # How much tax/duty
    ELIGIBILITY = "eligibility"  # Am I eligible/exempt
    EXEMPTION = "exemption"  # Same as eligibility, for compatibility
    PROCESS = "process"  # How to apply/pay/lodge
    DEADLINE = "deadline"  # When is it due
    PENALTY = "penalty"  # What are the penalties
    DEFINITION = "definition"  # What is this term/concept
    SCENARIO = "scenario"  # What happens if...
    COMPLIANCE = "compliance"  # How to comply/requirements
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of question classification"""
    revenue_type: RevenueType
    question_intent: QuestionIntent
    confidence: float
    key_entities: List[str]  # Dollar amounts, dates, property types, etc.
    source_requirements: List[str]  # What types of sources needed
    search_terms: List[str]  # Optimized search terms for this classification
    all_revenue_types: List[RevenueType]  # All applicable tax types identified
    requires_multi_tax_analysis: bool  # Whether this needs multiple tax calculations
    is_simple_calculation: bool  # True for direct "how much tax" questions with specific amounts


class ClassificationAgent:
    """
    Classifies questions to determine revenue type and intent for targeted sourcing
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Load comprehensive revenue data
        self._load_revenue_data()

        # Build dynamic keyword mappings from loaded data
        self.revenue_keywords = self._build_keyword_mappings()

        # Build intent keywords mapping
        self.intent_keywords = self._build_intent_keywords()

    def _load_revenue_data(self):
        """Load comprehensive revenue type data from JSON"""
        try:
            json_path = Path(__file__).parent.parent / 'data' / 'nsw_revenue_comprehensive_list.json'
            with open(json_path, 'r') as f:
                self.revenue_data = json.load(f)
                logger.info(f"Loaded {self.revenue_data['metadata']['total_revenue_types']} revenue types")
        except Exception as e:
            logger.warning(f"Could not load comprehensive revenue data: {e}")
            self.revenue_data = None

    def _build_keyword_mappings(self):
        """Build dynamic keyword mappings from revenue data"""
        keywords = {}

        # Comprehensive keyword mappings for all revenue types
        keywords[RevenueType.TRANSFER_DUTY] = [
            "stamp duty", "transfer duty", "conveyance", "purchase", "property transfer",
            "dutiable transaction", "first home", "concession", "surcharge"
        ]
        keywords[RevenueType.PAYROLL_TAX] = [
            "payroll tax", "payroll", "wages", "salary", "employee", "employer",
            "threshold", "grouping", "contractor", "1.2 million", "5.45%"
        ]
        keywords[RevenueType.LAND_TAX] = [
            "land tax", "property tax", "unimproved value", "principal residence", "ppor",
            "land value", "property assessment", "$969,000", "premium property"
        ]
        keywords[RevenueType.MOTOR_VEHICLE_DUTY] = [
            "motor vehicle", "vehicle duty", "car registration", "vehicle transfer",
            "electric vehicle", "luxury car", "green slip"
        ]
        keywords[RevenueType.GAMING_MACHINE_TAX] = [
            "gaming", "poker machine", "gaming machine", "club", "hotel gaming",
            "gaming tax", "gambling"
        ]
        keywords[RevenueType.BETTING_TAX] = [
            "betting", "wagering", "bookmaker", "point of consumption", "poc tax",
            "sports betting", "online betting"
        ]
        keywords[RevenueType.COAL_ROYALTY] = [
            "coal", "mining royalty", "coal royalty", "mineral extraction", "mining lease"
        ]
        keywords[RevenueType.MINERAL_ROYALTY] = [
            "mineral", "mining", "royalty", "ore", "extraction", "quarrying"
        ]
        keywords[RevenueType.PETROLEUM_ROYALTY] = [
            "petroleum", "oil", "gas", "natural gas", "wellhead", "offshore petroleum"
        ]
        keywords[RevenueType.PARKING_SPACE_LEVY] = [
            "parking", "parking space", "parking levy", "cbd parking", "commercial parking"
        ]
        keywords[RevenueType.FIRST_HOME_OWNER_GRANT] = [
            "first home", "fhog", "new home grant", "$10,000 grant", "first buyer"
        ]
        keywords[RevenueType.EMERGENCY_SERVICES_LEVY] = [
            "emergency services", "esl", "fire levy", "emergency levy", "property levy"
        ]
        keywords[RevenueType.WASTE_LEVY] = [
            "waste", "landfill", "waste levy", "environmental levy", "disposal levy"
        ]
        keywords[RevenueType.PENALTY_NOTICES] = [
            "fine", "penalty", "infringement", "penalty notice", "enforcement", "sdro"
        ]
        keywords[RevenueType.FOREIGN_PURCHASER_DUTY] = [
            "foreign", "foreign buyer", "foreign purchaser", "8%", "surcharge", "overseas"
        ]
        keywords[RevenueType.REVENUE_ADMINISTRATION] = [
            "objection", "appeal", "assessment", "revenue nsw", "compliance", "audit",
            "payment plan", "hardship", "administration"
        ]

        # Add all other revenue types with basic keywords
        for revenue_type in RevenueType:
            if revenue_type not in keywords and revenue_type != RevenueType.UNKNOWN:
                # Generate basic keywords from the enum name
                name = revenue_type.value.replace('_', ' ')
                keywords[revenue_type] = [name, revenue_type.value]

        return keywords

    def _build_intent_keywords(self):
        """Build intent keyword mappings"""
        return {
            QuestionIntent.CALCULATION: [
                "how much", "calculate", "amount", "cost", "rate", "percentage", "$", "total",
                "payroll tax for", "tax on", "owe", "owed", "liable", "liability", "due",
                "revenue", "wages", "salary", "income", "earnings", "million", "thousand"
            ],
            QuestionIntent.ELIGIBILITY: [
                "eligible", "qualify", "concession", "discount"
            ],
            QuestionIntent.EXEMPTION: [
                "exemption", "exempt", "exception", "exclude", "excluded"
            ],
            QuestionIntent.PROCESS: [
                "how to", "apply", "lodge", "submit", "pay", "process", "steps", "procedure"
            ],
            QuestionIntent.DEADLINE: [
                "when", "due", "deadline", "by when", "date", "timeline", "period"
            ],
            QuestionIntent.PENALTY: [
                "penalty", "fine", "consequences", "what happens if", "late", "non-payment"
            ],
            QuestionIntent.DEFINITION: [
                "what is", "define", "meaning", "explanation", "definition"
            ],
            QuestionIntent.SCENARIO: [
                "what if", "scenario", "situation", "case", "example", "what happens"
            ],
            QuestionIntent.COMPLIANCE: [
                "comply", "requirement", "must", "obligation", "rules", "regulations"
            ]
        }

    def classify_question(self, question: str) -> ClassificationResult:
        """
        Classify a question to determine revenue type and intent

        Args:
            question: User's question

        Returns:
            ClassificationResult with classification details
        """
        logger.info(f"Classifying question: {question}")

        # Step 1: Detect all applicable revenue types
        all_revenue_types = self._classify_all_revenue_types(question)
        primary_revenue_type = all_revenue_types[0] if all_revenue_types else RevenueType.UNKNOWN
        requires_multi_tax = len(all_revenue_types) > 1

        # Step 2: Classify intent
        question_intent = self._classify_intent(question)

        # Step 3: Extract entities (amounts, dates, etc.)
        entities = self._extract_entities(question)

        # Step 4: Calculate initial confidence
        confidence = self._calculate_confidence(question, primary_revenue_type, question_intent)

        # Step 5: Always use enhanced LLM analysis for better understanding
        llm_result = self._llm_classify(question)
        is_simple_calculation = False

        if llm_result:
            # Override with LLM analysis if available
            if 'revenue_type' in llm_result:
                try:
                    primary_revenue_type = RevenueType(llm_result['revenue_type'])
                except (ValueError, AttributeError, TypeError):
                    # Keep existing classification on any enum conversion error
                    pass

            if 'intent' in llm_result:
                try:
                    question_intent = QuestionIntent(llm_result['intent'])
                except (ValueError, AttributeError, TypeError):
                    # Keep existing classification on any enum conversion error
                    pass

            # Extract simple calculation flag
            is_simple_calculation = llm_result.get('is_simple_calculation', False)

            # Update multi-tax analysis from LLM
            if llm_result.get('is_multi_tax_question', False):
                requires_multi_tax = True
                # Update all_revenue_types from LLM analysis
                llm_tax_types = llm_result.get('all_tax_types', [])
                if llm_tax_types:
                    try:
                        converted_types = []
                        for tax_type in llm_tax_types:
                            if tax_type == 'parking_space_levy':
                                # Map parking space levy to duties_general for now
                                converted_types.append(RevenueType.DUTIES_GENERAL)
                            else:
                                converted_types.append(RevenueType(tax_type))
                        all_revenue_types = converted_types
                        primary_revenue_type = all_revenue_types[0] if all_revenue_types else primary_revenue_type
                    except (ValueError, AttributeError, TypeError):
                        # Keep existing classification on error
                        pass

            # Update entities with LLM-extracted amounts
            llm_amounts = llm_result.get('extracted_amounts', [])
            entities.extend(llm_amounts)
            entities = list(set(entities))  # Remove duplicates

            # Update confidence based on LLM confidence
            llm_confidence = llm_result.get('confidence', 'medium')
            if llm_confidence == 'high':
                confidence = max(confidence, 0.8)
            elif llm_confidence == 'low':
                confidence = min(confidence, 0.4)

        # Step 6: Determine source requirements for all tax types
        source_requirements = self._determine_multi_tax_requirements(all_revenue_types, question_intent)

        # Step 7: Generate optimized search terms
        search_terms = self._generate_search_terms(question, primary_revenue_type, question_intent, entities)

        result = ClassificationResult(
            revenue_type=primary_revenue_type,
            question_intent=question_intent,
            confidence=confidence,
            key_entities=entities,
            source_requirements=source_requirements,
            search_terms=search_terms,
            all_revenue_types=all_revenue_types,
            requires_multi_tax_analysis=requires_multi_tax,
            is_simple_calculation=is_simple_calculation
        )

        logger.info(f"Classification result: {primary_revenue_type.value}, {question_intent.value}, confidence: {confidence:.2f}, multi-tax: {requires_multi_tax}")
        return result

    def _classify_revenue_type(self, question: str) -> RevenueType:
        """Classify revenue type using keyword matching"""
        question_lower = question.lower()

        scores = {}
        for revenue_type, keywords in self.revenue_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                scores[revenue_type] = score

        if scores:
            return max(scores, key=scores.get)
        return RevenueType.UNKNOWN

    def _classify_intent(self, question: str) -> QuestionIntent:
        """Classify question intent using keyword matching"""
        question_lower = question.lower()

        scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                scores[intent] = score

        if scores:
            return max(scores, key=scores.get)
        return QuestionIntent.UNKNOWN

    def _extract_entities(self, question: str) -> List[str]:
        """Extract key entities from the question"""
        import re

        entities = []

        # Extract dollar amounts
        money_pattern = r'\$[\d,]+(?:\.\d+)?[kmb]?'
        money_matches = re.findall(money_pattern, question, re.IGNORECASE)
        entities.extend(money_matches)

        # Extract percentages
        percent_pattern = r'\d+(?:\.\d+)?%'
        percent_matches = re.findall(percent_pattern, question)
        entities.extend(percent_matches)

        # Extract years
        year_pattern = r'\b(19|20)\d{2}\b'
        year_matches = re.findall(year_pattern, question)
        entities.extend(year_matches)

        # Extract numbers (property counts, etc.)
        number_pattern = r'\b\d+\s*(?:properties|property|business|employee|year)\b'
        number_matches = re.findall(number_pattern, question, re.IGNORECASE)
        entities.extend(number_matches)

        return list(set(entities))

    def _llm_classify(self, question: str) -> Optional[Dict]:
        """Use LLM for refined classification when keyword matching fails"""
        try:
            prompt = f"""
            NSW REVENUE QUESTION ANALYSIS

            Question: "{question}"

            CRITICAL: Look for MULTIPLE tax types in this question. Many questions involve combined calculations.

            ANALYSIS INSTRUCTIONS:
            1. What is the user actually asking for? Are they asking:
               - For a specific dollar amount? (calculation)
               - How to do something? (process)
               - Whether they qualify for something? (eligibility)
               - What a term means? (definition)
               - What happens in a scenario? (scenario)
               - About deadlines or timing? (deadline)
               - About penalties or consequences? (penalty)
               - About compliance requirements? (compliance)

            2. IDENTIFY ALL NSW tax/duty types mentioned:
               - payroll_tax (wages, employees, business payroll)
               - land_tax (property, land value, residential properties)
               - stamp_duty (property purchase, conveyance, transfer)
               - duties_general (motor vehicle, insurance, mortgage)
               - revenue_administration (objections, appeals, assessments)
               - fines_penalties (late payment, non-compliance)
               - parking_space_levy (parking spaces, commercial properties)
               - unknown (if unclear or outside NSW revenue scope)

            3. Is this a multi-part calculation with multiple tax types?
               - Look for "and", property values + payroll, multiple components
               - Example: "payroll of $X and properties worth $Y"

            4. Is this a simple calculation question with specific amounts?
               - Look for dollar amounts, percentages, "how much", "calculate"
               - These need direct numerical answers

            Respond with JSON:
            {{"revenue_type": "...", "intent": "...", "is_simple_calculation": true/false, "is_multi_tax_question": true/false, "all_tax_types": ["type1", "type2"], "extracted_amounts": ["$X", "$Y"], "confidence": "high/medium/low"}}
            """

            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )

            import json
            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.warning(f"LLM classification failed: {e}")
            return None

    def _determine_source_requirements(self, revenue_type: RevenueType, intent: QuestionIntent) -> List[str]:
        """Determine what types of sources are needed"""
        requirements = []

        # Base requirement for all questions
        requirements.append("legislation")

        # Revenue type specific requirements - expand to all major types
        if revenue_type in [RevenueType.PAYROLL_TAX, RevenueType.LAND_TAX, RevenueType.TRANSFER_DUTY,
                           RevenueType.MOTOR_VEHICLE_DUTY, RevenueType.GAMING_MACHINE_TAX,
                           RevenueType.FOREIGN_PURCHASER_DUTY, RevenueType.PARKING_SPACE_LEVY]:
            requirements.append("current_rates")
            requirements.append("exemptions")

        # Intent specific requirements
        if intent == QuestionIntent.CALCULATION:
            requirements.extend(["rates", "thresholds", "calculation_examples"])
        elif intent == QuestionIntent.PROCESS:
            requirements.extend(["forms", "procedures", "deadlines"])
        elif intent == QuestionIntent.PENALTY:
            requirements.extend(["penalty_rates", "enforcement_procedures"])
        elif intent == QuestionIntent.DEADLINE:
            requirements.extend(["due_dates", "payment_schedules"])

        return list(set(requirements))

    def _generate_search_terms(self, question: str, revenue_type: RevenueType,
                             intent: QuestionIntent, entities: List[str]) -> List[str]:
        """Generate optimized search terms for this specific classification"""
        search_terms = []

        # Add revenue type specific terms
        if revenue_type != RevenueType.UNKNOWN:
            search_terms.extend(self.revenue_keywords[revenue_type][:3])  # Top 3 keywords

        # Add intent specific terms
        if intent != QuestionIntent.UNKNOWN:
            search_terms.extend(self.intent_keywords[intent][:2])  # Top 2 keywords

        # Add entities
        search_terms.extend(entities)

        # Add specific combinations
        if revenue_type == RevenueType.PAYROLL_TAX and intent == QuestionIntent.CALCULATION:
            search_terms.extend(["payroll tax rate", "threshold calculation"])
        elif revenue_type == RevenueType.LAND_TAX and intent == QuestionIntent.EXEMPTION:
            search_terms.extend(["land tax exemption", "primary residence"])
        elif revenue_type == RevenueType.TRANSFER_DUTY and intent == QuestionIntent.CALCULATION:
            search_terms.extend(["stamp duty calculator", "conveyance duty rate", "transfer duty calculator"])

        return list(set(search_terms))

    def _calculate_confidence(self, question: str, revenue_type: RevenueType,
                            intent: QuestionIntent) -> float:
        """Calculate confidence score for the classification"""
        confidence = 0.0

        # Base confidence from successful classification
        if revenue_type != RevenueType.UNKNOWN:
            confidence += 0.5
        if intent != QuestionIntent.UNKNOWN:
            confidence += 0.3

        # Boost for specific keyword matches
        question_lower = question.lower()

        # Check for exact revenue type matches
        exact_matches = {
            "payroll tax": RevenueType.PAYROLL_TAX,
            "land tax": RevenueType.LAND_TAX,
            "stamp duty": RevenueType.TRANSFER_DUTY,
            "transfer duty": RevenueType.TRANSFER_DUTY
        }

        for term, rtype in exact_matches.items():
            if term in question_lower and revenue_type == rtype:
                confidence += 0.2
                break

        return min(confidence, 1.0)

    def _classify_all_revenue_types(self, question: str) -> List[RevenueType]:
        """Detect all applicable revenue types in the question"""
        question_lower = question.lower()
        detected_types = []

        # Check for each revenue type
        for revenue_type, keywords in self.revenue_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question_lower)
            if score > 0:
                detected_types.append((revenue_type, score))

        # Special detection for property-related queries (land tax)
        property_indicators = ["properties", "property", "land", "real estate", "worth"]
        if any(indicator in question_lower for indicator in property_indicators):
            detected_types.append((RevenueType.LAND_TAX, 2))

        # Special detection for payroll/wages (payroll tax)
        payroll_indicators = ["payroll", "wages", "salary", "employees"]
        if any(indicator in question_lower for indicator in payroll_indicators):
            detected_types.append((RevenueType.PAYROLL_TAX, 2))

        # Sort by score and return unique types
        detected_types.sort(key=lambda x: x[1], reverse=True)
        return [rtype for rtype, score in detected_types if rtype not in [dt[0] for dt in detected_types[:detected_types.index((rtype, score))]]]

    def _determine_multi_tax_requirements(self, revenue_types: List[RevenueType], intent: QuestionIntent) -> List[str]:
        """Determine source requirements for multiple tax types"""
        requirements = []

        for revenue_type in revenue_types:
            # Add base requirement for this tax type
            requirements.append("legislation")

            # Expanded to cover all major revenue types
            if revenue_type in [RevenueType.PAYROLL_TAX, RevenueType.LAND_TAX, RevenueType.TRANSFER_DUTY,
                              RevenueType.FOREIGN_PURCHASER_DUTY, RevenueType.MOTOR_VEHICLE_DUTY,
                              RevenueType.GAMING_MACHINE_TAX, RevenueType.BETTING_TAX,
                              RevenueType.COAL_ROYALTY, RevenueType.MINERAL_ROYALTY,
                              RevenueType.PARKING_SPACE_LEVY, RevenueType.EMERGENCY_SERVICES_LEVY]:
                requirements.extend(["current_rates", "exemptions", "thresholds"])

            # Intent specific requirements
            if intent == QuestionIntent.CALCULATION:
                requirements.extend(["rates", "calculation_examples"])

        return list(set(requirements))

    def _get_all_revenue_types_for_prompt(self) -> str:
        """Get formatted list of all revenue types for LLM prompt"""
        categories = {
            "Property Related": [
                "transfer_duty (stamp duty on property purchases)",
                "foreign_purchaser_duty (8% surcharge for foreign buyers)",
                "land_tax (annual tax on land value)",
                "parking_space_levy (Sydney CBD parking)",
                "premium_property_tax (2% on properties over $5M)"
            ],
            "Business Taxation": [
                "payroll_tax (5.45% on wages over $1.2M)",
                "payroll_tax_rebate (rebates and incentives)",
                "contractor_provisions (contractor payments)"
            ],
            "Motor Vehicle": [
                "motor_vehicle_duty (3-5% on vehicle purchase)",
                "vehicle_registration (annual fees)",
                "ctp_insurance_levy (compulsory third party)",
                "electric_vehicle_exemption (EV incentives)"
            ],
            "Gaming and Liquor": [
                "gaming_machine_tax (poker machines)",
                "betting_tax (wagering and betting)",
                "point_of_consumption_tax (online betting)",
                "liquor_licensing_fees"
            ],
            "Mining and Resources": [
                "coal_royalty (coal extraction)",
                "mineral_royalty (other minerals)",
                "petroleum_royalty (oil and gas)",
                "quarrying_royalty (quarry materials)"
            ],
            "Environmental and Levies": [
                "waste_levy (landfill and disposal)",
                "emergency_services_levy (property levy)",
                "health_insurance_levy"
            ],
            "Grants and Assistance": [
                "first_home_owner_grant ($10,000 for new homes)",
                "shared_equity_scheme",
                "energy_savings_scheme"
            ],
            "Fines and Administration": [
                "penalty_notices (fines and infringements)",
                "revenue_administration (objections, appeals)",
                "unclaimed_money"
            ]
        }

        result = ""
        for category, types in categories.items():
            result += f"               {category}:\n"
            for tax_type in types:
                result += f"               - {tax_type}\n"

        return result


def main():
    """Test the classification agent"""
    agent = ClassificationAgent()

    test_questions = [
        "What is the payroll tax rate for a business with $2 million in wages?",
        "How do I calculate land tax for 3 properties worth $2.3 million?",
        "When is stamp duty due on a property purchase?",
        "What are the penalties for late payroll tax payment?",
        "Am I eligible for first home buyer stamp duty exemption?",
        "A customer has passed away and owned a business with $34,444 owing in payroll tax"
    ]

    for question in test_questions:
        print(f"\nQuestion: {question}")
        result = agent.classify_question(question)
        print(f"Revenue Type: {result.revenue_type.value}")
        print(f"Intent: {result.question_intent.value}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Entities: {result.key_entities}")
        print(f"Search Terms: {result.search_terms[:5]}")  # Show first 5


if __name__ == "__main__":
    main()