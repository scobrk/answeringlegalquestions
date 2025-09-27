"""
Rate Calculation Service for NSW Revenue
Provides accurate tax calculations using current rate schedules
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, date
import logging
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

@dataclass
class TaxCalculationResult:
    """Result of a tax calculation"""
    tax_type: str
    total_tax: Decimal
    breakdown: List[Dict[str, Any]]
    exemptions_applied: List[str]
    concessions_applied: List[str]
    calculation_date: datetime
    confidence: float
    warnings: List[str]
    additional_charges: Dict[str, Decimal]

@dataclass
class RateThreshold:
    """Represents a rate threshold"""
    min_value: Decimal
    max_value: Optional[Decimal]
    rate: Decimal
    rate_type: str  # 'percentage' or 'fixed'
    fixed_amount: Decimal
    description: str

class RateCalculationService:
    """
    Advanced rate calculation service for NSW Revenue taxes
    """

    def __init__(self, metadata_dir: str = "./data/metadata"):
        self.metadata_dir = Path(metadata_dir)
        self.rate_schedules = {}
        self.calculation_rules = {}

        # Load rate schedules
        self._load_rate_schedules()
        self._load_calculation_rules()

    def _load_rate_schedules(self) -> None:
        """Load all rate schedules from metadata files"""
        try:
            for rate_file in self.metadata_dir.glob("*_rates_*.json"):
                with open(rate_file, 'r') as f:
                    rate_data = json.load(f)

                tax_type = rate_data.get('tax_type')
                if tax_type:
                    self.rate_schedules[tax_type] = rate_data
                    logger.info(f"Loaded rate schedule for {tax_type}")

        except Exception as e:
            logger.error(f"Error loading rate schedules: {e}")

    def _load_calculation_rules(self) -> None:
        """Load tax-specific calculation rules"""
        self.calculation_rules = {
            'land_tax': {
                'rounding_rule': 'round_to_cent',
                'minimum_tax': Decimal('0'),
                'calculation_method': 'progressive_tiered',
                'exemption_rules': {
                    'principal_place_of_residence': {
                        'threshold': Decimal('755000'),
                        'applies_to': 'all_residential'
                    }
                }
            },
            'payroll_tax': {
                'rounding_rule': 'round_to_dollar',
                'minimum_tax': Decimal('0'),
                'calculation_method': 'flat_rate_above_threshold',
                'threshold': Decimal('1300000'),  # Annual threshold
                'monthly_threshold': Decimal('108333')  # Monthly threshold
            },
            'duties': {
                'rounding_rule': 'round_to_cent',
                'minimum_tax': Decimal('0'),
                'calculation_method': 'progressive_tiered',
                'concessions': {
                    'first_home_buyer': {
                        'full_exemption_threshold': Decimal('650000'),
                        'partial_exemption_max': Decimal('800000')
                    }
                }
            }
        }

    def calculate_land_tax(self,
                          property_value: Decimal,
                          property_type: str = 'residential',
                          is_principal_place_of_residence: bool = False,
                          calculation_year: int = 2024) -> TaxCalculationResult:
        """Calculate land tax for a property"""

        if 'land_tax' not in self.rate_schedules:
            raise ValueError("Land tax rate schedule not found")

        rate_schedule = self.rate_schedules['land_tax']
        property_value = Decimal(str(property_value))

        # Check for principal place of residence exemption
        exemptions_applied = []
        if is_principal_place_of_residence:
            exemptions_applied.append('principal_place_of_residence')
            return TaxCalculationResult(
                tax_type='land_tax',
                total_tax=Decimal('0'),
                breakdown=[{
                    'description': 'Principal place of residence exemption',
                    'calculation': 'Exempt',
                    'amount': Decimal('0')
                }],
                exemptions_applied=exemptions_applied,
                concessions_applied=[],
                calculation_date=datetime.now(),
                confidence=1.0,
                warnings=[],
                additional_charges={}
            )

        # Get rate table
        rate_table = rate_schedule['rate_tables']['general_rate']
        thresholds = rate_table['thresholds']

        # Calculate progressive tax
        total_tax = Decimal('0')
        breakdown = []
        remaining_value = property_value

        for threshold_data in thresholds:
            threshold = RateThreshold(
                min_value=Decimal(str(threshold_data['min_value'])),
                max_value=Decimal(str(threshold_data['max_value'])) if threshold_data['max_value'] else None,
                rate=Decimal(str(threshold_data['rate'])),
                rate_type=threshold_data['rate_type'],
                fixed_amount=Decimal(str(threshold_data['fixed_amount'])),
                description=threshold_data['description']
            )

            if remaining_value <= 0:
                break

            # Calculate tax for this threshold
            if property_value > threshold.min_value:
                if threshold.max_value:
                    taxable_in_band = min(remaining_value, threshold.max_value - threshold.min_value + 1)
                else:
                    taxable_in_band = remaining_value

                if taxable_in_band > 0:
                    band_tax = taxable_in_band * threshold.rate
                    total_tax += band_tax + threshold.fixed_amount

                    breakdown.append({
                        'threshold': f"${threshold.min_value:,.0f} - {f'${threshold.max_value:,.0f}' if threshold.max_value else 'unlimited'}",
                        'taxable_amount': taxable_in_band,
                        'rate': f"{threshold.rate * 100:.2f}%",
                        'tax_amount': band_tax + threshold.fixed_amount,
                        'description': threshold.description
                    })

                    remaining_value -= taxable_in_band

        # Round according to rules
        total_tax = self._apply_rounding('land_tax', total_tax)

        # Check for premium property tax (if over $3M)
        additional_charges = {}
        warnings = []
        if property_value > Decimal('3000000'):
            premium_tax = property_value * Decimal('0.02')  # 2% premium property tax
            additional_charges['premium_property_tax'] = premium_tax
            warnings.append("Premium property tax (2% surcharge) applies to properties over $3M")

        return TaxCalculationResult(
            tax_type='land_tax',
            total_tax=total_tax,
            breakdown=breakdown,
            exemptions_applied=exemptions_applied,
            concessions_applied=[],
            calculation_date=datetime.now(),
            confidence=1.0,
            warnings=warnings,
            additional_charges=additional_charges
        )

    def calculate_payroll_tax(self,
                            annual_payroll: Decimal,
                            calculation_period: str = 'annual',
                            calculation_year: int = 2024) -> TaxCalculationResult:
        """Calculate payroll tax"""

        if 'payroll_tax' not in self.rate_schedules:
            raise ValueError("Payroll tax rate schedule not found")

        rate_schedule = self.rate_schedules['payroll_tax']
        annual_payroll = Decimal(str(annual_payroll))

        # Get threshold and rate
        thresholds = rate_schedule['rate_tables']['general_rate']['thresholds']
        tax_free_threshold = Decimal(str(thresholds[0]['max_value']))  # $1.3M
        tax_rate = Decimal(str(thresholds[1]['rate']))  # 5.45%

        breakdown = []
        exemptions_applied = []

        # Check if below threshold
        if annual_payroll <= tax_free_threshold:
            exemptions_applied.append('below_threshold')
            breakdown.append({
                'description': f'Annual payroll below tax-free threshold of ${tax_free_threshold:,.0f}',
                'calculation': 'Exempt',
                'amount': Decimal('0')
            })
            total_tax = Decimal('0')
        else:
            # Calculate tax on excess
            taxable_payroll = annual_payroll - tax_free_threshold
            total_tax = taxable_payroll * tax_rate

            breakdown.append({
                'description': f'Tax-free threshold',
                'amount': tax_free_threshold,
                'tax': Decimal('0')
            })
            breakdown.append({
                'description': f'Taxable payroll (excess over threshold)',
                'amount': taxable_payroll,
                'rate': f'{tax_rate * 100:.2f}%',
                'tax': total_tax
            })

        # Adjust for calculation period
        if calculation_period == 'monthly':
            total_tax = total_tax / 12
            for item in breakdown:
                if 'tax' in item:
                    item['tax'] = item['tax'] / 12

        # Round according to rules
        total_tax = self._apply_rounding('payroll_tax', total_tax)

        return TaxCalculationResult(
            tax_type='payroll_tax',
            total_tax=total_tax,
            breakdown=breakdown,
            exemptions_applied=exemptions_applied,
            concessions_applied=[],
            calculation_date=datetime.now(),
            confidence=1.0,
            warnings=[],
            additional_charges={}
        )

    def calculate_stamp_duty(self,
                           property_value: Decimal,
                           property_type: str = 'residential',
                           is_first_home_buyer: bool = False,
                           is_foreign_purchaser: bool = False,
                           calculation_year: int = 2024) -> TaxCalculationResult:
        """Calculate stamp duty (conveyance duty)"""

        property_value = Decimal(str(property_value))
        breakdown = []
        exemptions_applied = []
        concessions_applied = []
        additional_charges = {}
        warnings = []

        # Basic residential rates (simplified - would load from rate schedule)
        rate_bands = [
            {'min': 0, 'max': 14000, 'rate': 0.0125, 'fixed': 0},
            {'min': 14001, 'max': 32000, 'rate': 0.015, 'fixed': 175},
            {'min': 32001, 'max': 85000, 'rate': 0.0175, 'fixed': 445},
            {'min': 85001, 'max': 319000, 'rate': 0.035, 'fixed': 1372.50},
            {'min': 319001, 'max': 1064000, 'rate': 0.045, 'fixed': 9562.50},
            {'min': 1064001, 'max': None, 'rate': 0.055, 'fixed': 43087.50}
        ]

        # Check first home buyer exemption
        if is_first_home_buyer:
            if property_value <= Decimal('650000'):
                exemptions_applied.append('first_home_buyer_full_exemption')
                return TaxCalculationResult(
                    tax_type='stamp_duty',
                    total_tax=Decimal('0'),
                    breakdown=[{
                        'description': 'First home buyer full exemption (property value ≤ $650,000)',
                        'calculation': 'Exempt',
                        'amount': Decimal('0')
                    }],
                    exemptions_applied=exemptions_applied,
                    concessions_applied=concessions_applied,
                    calculation_date=datetime.now(),
                    confidence=1.0,
                    warnings=warnings,
                    additional_charges=additional_charges
                )
            elif property_value <= Decimal('800000'):
                concessions_applied.append('first_home_buyer_partial_exemption')

        # Calculate basic stamp duty
        total_duty = Decimal('0')
        remaining_value = property_value

        for band in rate_bands:
            min_value = Decimal(str(band['min']))
            max_value = Decimal(str(band['max'])) if band['max'] else None
            rate = Decimal(str(band['rate']))
            fixed_amount = Decimal(str(band['fixed']))

            if remaining_value <= 0:
                break

            if property_value > min_value:
                if max_value:
                    taxable_in_band = min(remaining_value, max_value - min_value + 1)
                else:
                    taxable_in_band = remaining_value

                if taxable_in_band > 0:
                    band_duty = (taxable_in_band * rate) + fixed_amount
                    total_duty += band_duty

                    breakdown.append({
                        'threshold': f"${min_value:,.0f} - {f'${max_value:,.0f}' if max_value else 'unlimited'}",
                        'taxable_amount': taxable_in_band,
                        'rate': f"{rate * 100:.2f}%",
                        'duty_amount': band_duty,
                        'description': f"Duty on amount in this band"
                    })

                    remaining_value -= taxable_in_band

        # Apply first home buyer concession if applicable
        if 'first_home_buyer_partial_exemption' in concessions_applied:
            # Calculate sliding scale reduction
            reduction_rate = (Decimal('800000') - property_value) / Decimal('150000')
            reduction_amount = total_duty * reduction_rate
            total_duty -= reduction_amount

            breakdown.append({
                'description': 'First home buyer partial exemption',
                'reduction_amount': reduction_amount,
                'final_duty': total_duty
            })

        # Add foreign purchaser additional duty if applicable
        if is_foreign_purchaser:
            foreign_duty = property_value * Decimal('0.08')  # 8% additional duty
            additional_charges['foreign_purchaser_additional_duty'] = foreign_duty
            warnings.append("Foreign purchaser additional duty (8%) applies")

        # Round to nearest dollar
        total_duty = total_duty.quantize(Decimal('1'), rounding=ROUND_HALF_UP)

        return TaxCalculationResult(
            tax_type='stamp_duty',
            total_tax=total_duty,
            breakdown=breakdown,
            exemptions_applied=exemptions_applied,
            concessions_applied=concessions_applied,
            calculation_date=datetime.now(),
            confidence=1.0,
            warnings=warnings,
            additional_charges=additional_charges
        )

    def _apply_rounding(self, tax_type: str, amount: Decimal) -> Decimal:
        """Apply tax-specific rounding rules"""
        rules = self.calculation_rules.get(tax_type, {})
        rounding_rule = rules.get('rounding_rule', 'round_to_cent')

        if rounding_rule == 'round_to_dollar':
            return amount.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        else:  # round_to_cent
            return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def calculate_combined_tax_scenario(self,
                                      scenario: Dict[str, Any]) -> Dict[str, TaxCalculationResult]:
        """Calculate taxes for a combined scenario (e.g., property purchase)"""
        results = {}

        # Property purchase scenario
        if scenario.get('transaction_type') == 'property_purchase':
            property_value = Decimal(str(scenario['property_value']))
            is_first_home_buyer = scenario.get('is_first_home_buyer', False)
            is_foreign_purchaser = scenario.get('is_foreign_purchaser', False)
            is_ppr = scenario.get('is_principal_place_of_residence', False)

            # Calculate stamp duty
            results['stamp_duty'] = self.calculate_stamp_duty(
                property_value=property_value,
                is_first_home_buyer=is_first_home_buyer,
                is_foreign_purchaser=is_foreign_purchaser
            )

            # Calculate ongoing land tax
            results['land_tax'] = self.calculate_land_tax(
                property_value=property_value,
                is_principal_place_of_residence=is_ppr
            )

        # Business scenario
        if scenario.get('entity_type') == 'business':
            annual_payroll = scenario.get('annual_payroll')
            if annual_payroll:
                results['payroll_tax'] = self.calculate_payroll_tax(
                    annual_payroll=Decimal(str(annual_payroll))
                )

        return results

    def get_available_tax_types(self) -> List[str]:
        """Get list of available tax types for calculation"""
        return list(self.rate_schedules.keys()) + ['stamp_duty']  # stamp_duty uses hardcoded rates

    def get_rate_schedule_info(self, tax_type: str) -> Optional[Dict[str, Any]]:
        """Get information about a rate schedule"""
        if tax_type in self.rate_schedules:
            schedule = self.rate_schedules[tax_type]
            return {
                'tax_type': tax_type,
                'effective_from': schedule.get('effective_from'),
                'effective_to': schedule.get('effective_to'),
                'rate_structure': schedule.get('rate_structure'),
                'last_updated': schedule.get('last_updated')
            }
        return None


def main():
    """Test the rate calculation service"""
    service = RateCalculationService()

    print("📊 Available tax types:", service.get_available_tax_types())

    # Test land tax calculation
    print("\n🏠 Land Tax Calculation:")
    print("Property value: $2,000,000 (not PPR)")
    land_tax_result = service.calculate_land_tax(
        property_value=Decimal('2000000'),
        is_principal_place_of_residence=False
    )
    print(f"Total land tax: ${land_tax_result.total_tax:,.2f}")
    for item in land_tax_result.breakdown:
        print(f"  {item}")

    # Test payroll tax calculation
    print("\n💼 Payroll Tax Calculation:")
    print("Annual payroll: $2,000,000")
    payroll_result = service.calculate_payroll_tax(
        annual_payroll=Decimal('2000000')
    )
    print(f"Total payroll tax: ${payroll_result.total_tax:,.2f}")
    for item in payroll_result.breakdown:
        print(f"  {item}")

    # Test stamp duty calculation
    print("\n🏡 Stamp Duty Calculation:")
    print("Property value: $800,000, First home buyer")
    duty_result = service.calculate_stamp_duty(
        property_value=Decimal('800000'),
        is_first_home_buyer=True
    )
    print(f"Total stamp duty: ${duty_result.total_tax:,.2f}")
    if duty_result.concessions_applied:
        print(f"Concessions applied: {duty_result.concessions_applied}")

    # Test combined scenario
    print("\n🏘️ Combined Property Purchase Scenario:")
    scenario = {
        'transaction_type': 'property_purchase',
        'property_value': 1200000,
        'is_first_home_buyer': False,
        'is_foreign_purchaser': False,
        'is_principal_place_of_residence': True
    }

    combined_results = service.calculate_combined_tax_scenario(scenario)
    for tax_type, result in combined_results.items():
        print(f"{tax_type}: ${result.total_tax:,.2f}")
        if result.exemptions_applied:
            print(f"  Exemptions: {result.exemptions_applied}")
        if result.warnings:
            print(f"  Warnings: {result.warnings}")


if __name__ == "__main__":
    main()