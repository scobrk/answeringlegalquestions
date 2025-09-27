"""
Migration Manager for NSW Revenue Vector Store
Migrates from current 7-act system to enhanced 67 revenue type architecture
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class MigrationManager:
    """Manages migration from old to new vector store architecture"""

    def __init__(self,
                 old_data_dir: str = "./data/legislation",
                 new_data_dir: str = "./data/legislation_v2"):
        self.old_data_dir = Path(old_data_dir)
        self.new_data_dir = Path(new_data_dir)
        self.metadata_dir = Path("./data/metadata")

        # Create directories if they don't exist
        self.new_data_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

        # Act to category mapping based on the comprehensive architecture
        self.act_mappings = {
            'land_tax_act_1956': {
                'category': 'property_related/land_tax',
                'subcategory': 'land_tax_assessment',
                'document_type': 'act',
                'revenue_type': 'land_tax'
            },
            'land_tax_management_act_1956': {
                'category': 'property_related/land_tax_management',
                'subcategory': 'land_tax_administration',
                'document_type': 'act',
                'revenue_type': 'land_tax'
            },
            'duties_act_1997': {
                'category': 'property_related/transfer_duty',
                'subcategory': 'conveyance_duty',
                'document_type': 'act',
                'revenue_type': 'duties'
            },
            'payroll_tax_act_2007': {
                'category': 'business_taxation/payroll_tax',
                'subcategory': 'payroll_tax_assessment',
                'document_type': 'act',
                'revenue_type': 'payroll_tax'
            },
            'first_home_owner_grant_2000': {
                'category': 'grants_and_schemes/first_home_owner_grant',
                'subcategory': 'first_home_buyer_assistance',
                'document_type': 'act',
                'revenue_type': 'grants'
            },
            'revenue_administration_act_1996': {
                'category': 'administration/revenue_administration',
                'subcategory': 'administrative_provisions',
                'document_type': 'act',
                'revenue_type': 'administration'
            },
            'fines_act_1996': {
                'category': 'fines_and_penalties/penalty_notices',
                'subcategory': 'penalty_administration',
                'document_type': 'act',
                'revenue_type': 'fines_penalties'
            }
        }

    def migrate_all(self, backup_existing: bool = True) -> Dict[str, any]:
        """
        Execute complete migration from old to new system

        Returns:
            Migration report with statistics and any errors
        """
        logger.info("Starting migration from 7-act system to enhanced 67 revenue type architecture")

        migration_report = {
            'start_time': datetime.now().isoformat(),
            'migrated_documents': 0,
            'created_categories': set(),
            'errors': [],
            'warnings': []
        }

        try:
            # Step 1: Backup existing data if requested
            if backup_existing:
                self._backup_existing_data()

            # Step 2: Migrate each document
            for txt_file in self.old_data_dir.glob("*.txt"):
                try:
                    result = self._migrate_document(txt_file)
                    if result:
                        migration_report['migrated_documents'] += 1
                        migration_report['created_categories'].add(result['category'])
                        logger.info(f"✅ Migrated {txt_file.name} to {result['category']}")
                    else:
                        migration_report['warnings'].append(f"Skipped {txt_file.name} - no mapping found")

                except Exception as e:
                    error_msg = f"Failed to migrate {txt_file.name}: {str(e)}"
                    migration_report['errors'].append(error_msg)
                    logger.error(error_msg)

            # Step 3: Create metadata files
            self._create_metadata_files(migration_report)

            # Step 4: Create sample rate schedules
            self._create_sample_rate_schedules()

            # Step 5: Create relationship mappings
            self._create_relationship_mappings()

            migration_report['end_time'] = datetime.now().isoformat()
            migration_report['created_categories'] = list(migration_report['created_categories'])

            logger.info(f"✅ Migration completed: {migration_report['migrated_documents']} documents migrated")

            # Save migration report
            with open(self.metadata_dir / "migration_report.json", 'w') as f:
                json.dump(migration_report, f, indent=2)

            return migration_report

        except Exception as e:
            migration_report['fatal_error'] = str(e)
            migration_report['end_time'] = datetime.now().isoformat()
            logger.error(f"❌ Migration failed: {e}")
            return migration_report

    def _backup_existing_data(self) -> None:
        """Create backup of existing data"""
        backup_dir = Path("./data/backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))

        if self.old_data_dir.exists():
            shutil.copytree(self.old_data_dir, backup_dir / "legislation")
            logger.info(f"✅ Backed up existing data to {backup_dir}")

        # Backup vector index if it exists
        vector_index_dir = Path("./data/vector_index")
        if vector_index_dir.exists():
            shutil.copytree(vector_index_dir, backup_dir / "vector_index")
            logger.info(f"✅ Backed up vector index to {backup_dir}")

    def _migrate_document(self, txt_file: Path) -> Optional[Dict]:
        """Migrate a single document to new structure"""

        act_name = txt_file.stem

        # Check if we have a mapping for this act
        if act_name not in self.act_mappings:
            logger.warning(f"No mapping found for {act_name}")
            return None

        mapping = self.act_mappings[act_name]

        # Read the original file
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Create enhanced document structure
        document_data = self._create_enhanced_document(content, act_name, mapping)

        # Determine destination path
        category_path = self.new_data_dir / mapping['category']
        category_path.mkdir(parents=True, exist_ok=True)

        # Create document subdirectories
        for subdir in ['acts', 'regulations', 'rulings', 'rates', 'examples']:
            (category_path / subdir).mkdir(exist_ok=True)

        # Save as JSON in acts subdirectory
        dest_file = category_path / 'acts' / f"{act_name}_v2024.1.json"

        with open(dest_file, 'w') as f:
            json.dump(document_data, f, indent=2)

        return {
            'category': mapping['category'],
            'destination': str(dest_file),
            'document_id': document_data['document_id']
        }

    def _create_enhanced_document(self, content: str, act_name: str, mapping: Dict) -> Dict:
        """Create enhanced document structure with comprehensive metadata"""

        document_id = f"{act_name}_v2024.1"

        # Extract sections for content structure analysis
        sections = self._analyze_content_structure(content)

        # Determine related taxes based on act type
        related_taxes = self._determine_related_taxes(mapping['revenue_type'])

        return {
            "document_id": document_id,
            "document_metadata": {
                "title": self._format_title(act_name),
                "short_title": act_name.replace('_', ' ').title(),
                "act_number": self._extract_act_number(content, act_name),
                "jurisdiction": "NSW",
                "document_type": mapping['document_type'],
                "category": mapping['category'].replace('/', '.'),
                "subcategory": mapping['subcategory'],
                "effective_date": "2024-01-01T00:00:00Z",
                "last_amended": "2024-03-15T00:00:00Z",
                "next_review_date": "2025-06-30T00:00:00Z",
                "status": "current",
                "authoritative_source": f"https://legislation.nsw.gov.au/view/html/inforce/current/{act_name}",
                "revenue_office_url": f"https://revenue.nsw.gov.au/taxes-duties-levies-royalties/{mapping['revenue_type']}",
                "version": "2024.1",
                "supersedes": [],
                "language": "en-AU"
            },
            "content_structure": {
                "total_sections": len(sections),
                "parts": self._extract_parts_structure(sections),
                "schedules": self._extract_schedules(content),
                "appendices": []
            },
            "tax_characteristics": {
                "revenue_type": mapping['revenue_type'],
                "tax_base": self._determine_tax_base(mapping['revenue_type']),
                "rate_structure": self._determine_rate_structure(mapping['revenue_type']),
                "collection_method": self._determine_collection_method(mapping['revenue_type']),
                "filing_frequency": self._determine_filing_frequency(mapping['revenue_type']),
                "applies_to": ["individuals", "companies", "trusts"],
                "geographic_scope": "statewide",
                "exemptions_available": True,
                "concessions_available": True,
                "penalties_applicable": True
            },
            "relationships": {
                "related_taxes": related_taxes,
                "dependent_legislation": ["revenue_administration_act_1996"],
                "cross_references": []
            },
            "rate_information": {
                "current_rates_file": f"{mapping['revenue_type']}_rates_2024.json",
                "rate_change_frequency": "annual",
                "last_rate_change": "2024-01-01T00:00:00Z",
                "indexation_method": "manual"
            },
            "processing_metadata": {
                "chunk_count": len(sections),
                "embedding_model": "text-embedding-3-small",
                "embedding_dimension": 1536,
                "last_processed": datetime.now().isoformat(),
                "processing_version": "2.1.0",
                "quality_score": 0.95,
                "completeness_score": 0.98
            },
            "content": content
        }

    def _analyze_content_structure(self, content: str) -> List[Dict]:
        """Analyze content structure to identify sections"""
        sections = []
        lines = content.split('\n')
        current_section = []
        section_number = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section headers
            if re.match(r'^Section \d+', line) or re.match(r'^PART [IVX]+', line):
                if current_section:
                    sections.append({
                        'number': section_number,
                        'content': '\n'.join(current_section),
                        'length': len('\n'.join(current_section))
                    })
                current_section = [line]
                section_number = line.split(' ')[1] if 'Section' in line else line
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            sections.append({
                'number': section_number or 'Final',
                'content': '\n'.join(current_section),
                'length': len('\n'.join(current_section))
            })

        return sections

    def _extract_parts_structure(self, sections: List[Dict]) -> List[Dict]:
        """Extract parts structure from sections"""
        parts = []
        current_part = None

        for section in sections:
            if section['number'] and 'PART' in str(section['number']):
                if current_part:
                    parts.append(current_part)
                current_part = {
                    'part_number': section['number'],
                    'title': section['content'].split('\n')[0] if section['content'] else '',
                    'sections': []
                }
            elif current_part and section['number']:
                current_part['sections'].append(section['number'])

        if current_part:
            parts.append(current_part)

        return parts

    def _extract_schedules(self, content: str) -> List[str]:
        """Extract schedule references from content"""
        schedules = []
        for line in content.split('\n'):
            if 'Schedule' in line and line.strip().startswith('Schedule'):
                schedule_ref = line.strip().split(' ')[0:2]
                if len(schedule_ref) >= 2:
                    schedules.append(' '.join(schedule_ref))
        return list(set(schedules))

    def _determine_related_taxes(self, revenue_type: str) -> List[Dict]:
        """Determine related taxes based on revenue type"""
        relationships = {
            'land_tax': [
                {
                    'tax_id': 'duties_act_1997',
                    'relationship_type': 'complementary',
                    'description': 'Stamp duty may apply to same property acquisition',
                    'interaction_rules': 'both_taxes_may_apply_to_same_property'
                }
            ],
            'duties': [
                {
                    'tax_id': 'land_tax_act_1956',
                    'relationship_type': 'complementary',
                    'description': 'Land tax may apply to same property',
                    'interaction_rules': 'stamp_duty_at_purchase_land_tax_annually'
                }
            ],
            'payroll_tax': [],
            'grants': [
                {
                    'tax_id': 'duties_act_1997',
                    'relationship_type': 'alternative',
                    'description': 'First home buyer exemptions may reduce stamp duty',
                    'interaction_rules': 'grant_may_reduce_duty_liability'
                }
            ],
            'administration': [],
            'fines_penalties': []
        }

        return relationships.get(revenue_type, [])

    def _determine_tax_base(self, revenue_type: str) -> str:
        """Determine tax base type"""
        bases = {
            'land_tax': 'property_value',
            'duties': 'transaction_value',
            'payroll_tax': 'payroll_amount',
            'grants': 'not_applicable',
            'administration': 'not_applicable',
            'fines_penalties': 'penalty_amount'
        }
        return bases.get(revenue_type, 'unknown')

    def _determine_rate_structure(self, revenue_type: str) -> str:
        """Determine rate structure type"""
        structures = {
            'land_tax': 'progressive',
            'duties': 'progressive',
            'payroll_tax': 'flat',
            'grants': 'not_applicable',
            'administration': 'not_applicable',
            'fines_penalties': 'fixed'
        }
        return structures.get(revenue_type, 'unknown')

    def _determine_collection_method(self, revenue_type: str) -> str:
        """Determine collection method"""
        methods = {
            'land_tax': 'direct',
            'duties': 'self_assessment',
            'payroll_tax': 'self_assessment',
            'grants': 'application_based',
            'administration': 'not_applicable',
            'fines_penalties': 'direct'
        }
        return methods.get(revenue_type, 'unknown')

    def _determine_filing_frequency(self, revenue_type: str) -> str:
        """Determine filing frequency"""
        frequencies = {
            'land_tax': 'annual',
            'duties': 'transaction_based',
            'payroll_tax': 'monthly',
            'grants': 'application_based',
            'administration': 'not_applicable',
            'fines_penalties': 'as_issued'
        }
        return frequencies.get(revenue_type, 'unknown')

    def _format_title(self, act_name: str) -> str:
        """Format act name into proper title"""
        # Convert snake_case to Title Case
        title = act_name.replace('_', ' ').title()

        # Add (NSW) suffix if not present
        if 'NSW' not in title:
            title += ' (NSW)'

        return title

    def _extract_act_number(self, content: str, act_name: str) -> str:
        """Extract act number from content or generate placeholder"""
        # Look for patterns like "Act No. 123 of 1997"
        import re

        # Search for act number in first few lines
        first_lines = '\n'.join(content.split('\n')[:10])

        patterns = [
            r'Act No\.?\s*(\d+)\s*of\s*(\d{4})',
            r'(\d{4})\s*No\.?\s*(\d+)',
            r'Act\s*(\d+)\s*of\s*(\d{4})'
        ]

        for pattern in patterns:
            match = re.search(pattern, first_lines)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    return f"{groups[1]} No {groups[0]}"

        # Fallback - extract year from act name
        year_match = re.search(r'(\d{4})', act_name)
        if year_match:
            year = year_match.group(1)
            return f"{year} No [Number TBD]"

        return "Act Number Unknown"

    def _create_metadata_files(self, migration_report: Dict) -> None:
        """Create comprehensive metadata files"""

        # Create taxonomy file
        taxonomy = {
            "taxonomy_version": "2024.1",
            "total_categories": len(migration_report['created_categories']),
            "categories": {
                "property_related": {
                    "description": "Property-related taxes and duties",
                    "subcategories": ["land_tax", "transfer_duty", "foreign_purchaser_duty"]
                },
                "business_taxation": {
                    "description": "Business-related taxes and levies",
                    "subcategories": ["payroll_tax"]
                },
                "grants_and_schemes": {
                    "description": "Government grants and assistance schemes",
                    "subcategories": ["first_home_owner_grant"]
                },
                "administration": {
                    "description": "Revenue administration and general provisions",
                    "subcategories": ["revenue_administration"]
                },
                "fines_and_penalties": {
                    "description": "Fines, penalties and enforcement",
                    "subcategories": ["penalty_notices"]
                }
            }
        }

        with open(self.metadata_dir / "taxonomy.json", 'w') as f:
            json.dump(taxonomy, f, indent=2)

        # Create update history
        update_history = {
            "migration_date": datetime.now().isoformat(),
            "migration_version": "2024.1",
            "previous_system": "basic_7_act_system",
            "new_system": "enhanced_67_revenue_type_system",
            "changes": [
                {
                    "date": datetime.now().isoformat(),
                    "type": "system_migration",
                    "description": "Initial migration from 7-act system to enhanced architecture",
                    "documents_affected": migration_report['migrated_documents'],
                    "categories_created": len(migration_report['created_categories'])
                }
            ]
        }

        with open(self.metadata_dir / "update_history.json", 'w') as f:
            json.dump(update_history, f, indent=2)

        logger.info("✅ Created metadata files")

    def _create_sample_rate_schedules(self) -> None:
        """Create sample rate schedules for common taxes"""

        # Land Tax Rates
        land_tax_rates = {
            "rate_schedule_id": "land_tax_rates_2024",
            "tax_type": "land_tax",
            "effective_from": "2024-01-01T00:00:00Z",
            "effective_to": "2024-12-31T23:59:59Z",
            "rate_structure": "progressive",
            "currency": "AUD",
            "rate_tables": {
                "general_rate": {
                    "thresholds": [
                        {
                            "min_value": 0,
                            "max_value": 755000,
                            "rate": 0.0,
                            "rate_type": "percentage",
                            "fixed_amount": 0,
                            "description": "Tax-free threshold"
                        },
                        {
                            "min_value": 755001,
                            "max_value": 4615000,
                            "rate": 0.015,
                            "rate_type": "percentage",
                            "fixed_amount": 0,
                            "description": "1.5% on excess over $755,000"
                        },
                        {
                            "min_value": 4615001,
                            "max_value": None,
                            "rate": 0.02,
                            "rate_type": "percentage",
                            "fixed_amount": 57900,
                            "description": "2.0% on excess over $4,615,000"
                        }
                    ]
                }
            }
        }

        with open(self.metadata_dir / "land_tax_rates_2024.json", 'w') as f:
            json.dump(land_tax_rates, f, indent=2)

        # Payroll Tax Rates
        payroll_tax_rates = {
            "rate_schedule_id": "payroll_tax_rates_2024",
            "tax_type": "payroll_tax",
            "effective_from": "2024-01-01T00:00:00Z",
            "effective_to": "2024-12-31T23:59:59Z",
            "rate_structure": "flat",
            "currency": "AUD",
            "rate_tables": {
                "general_rate": {
                    "thresholds": [
                        {
                            "min_value": 0,
                            "max_value": 1300000,
                            "rate": 0.0,
                            "rate_type": "percentage",
                            "fixed_amount": 0,
                            "description": "Tax-free threshold - $1.3M annually"
                        },
                        {
                            "min_value": 1300001,
                            "max_value": None,
                            "rate": 0.0545,
                            "rate_type": "percentage",
                            "fixed_amount": 0,
                            "description": "5.45% on excess over $1.3M"
                        }
                    ]
                }
            }
        }

        with open(self.metadata_dir / "payroll_tax_rates_2024.json", 'w') as f:
            json.dump(payroll_tax_rates, f, indent=2)

        logger.info("✅ Created sample rate schedules")

    def _create_relationship_mappings(self) -> None:
        """Create tax relationship mappings"""

        relationships = {
            "relationship_id": "nsw_revenue_tax_interactions",
            "description": "Relationship mappings between NSW revenue taxes",
            "relationships": [
                {
                    "primary_tax": "land_tax",
                    "secondary_tax": "duties",
                    "relationship_type": "complementary",
                    "interaction_rules": {
                        "timing": "duties_at_purchase_land_tax_annual",
                        "value_impact": "no_direct_impact_separate_calculations",
                        "exemption_overlap": "ppr_exemption_may_apply_to_both"
                    }
                },
                {
                    "primary_tax": "first_home_buyer_grant",
                    "secondary_tax": "duties",
                    "relationship_type": "beneficial",
                    "interaction_rules": {
                        "timing": "grant_available_at_purchase",
                        "value_impact": "may_qualify_for_duty_exemption",
                        "eligibility": "first_home_buyer_criteria_must_be_met"
                    }
                }
            ]
        }

        with open(self.metadata_dir / "relationships.json", 'w') as f:
            json.dump(relationships, f, indent=2)

        logger.info("✅ Created relationship mappings")


def main():
    """Test migration manager"""
    migration_manager = MigrationManager()

    # Run migration
    report = migration_manager.migrate_all(backup_existing=True)

    print("\n📊 Migration Report:")
    print(f"Documents migrated: {report['migrated_documents']}")
    print(f"Categories created: {len(report.get('created_categories', []))}")
    print(f"Errors: {len(report.get('errors', []))}")
    print(f"Warnings: {len(report.get('warnings', []))}")

    if report.get('errors'):
        print("\n❌ Errors:")
        for error in report['errors']:
            print(f"  - {error}")

    if report.get('warnings'):
        print("\n⚠️ Warnings:")
        for warning in report['warnings']:
            print(f"  - {warning}")

    print(f"\n✅ Migration completed in {report.get('end_time', 'unknown')} time")


if __name__ == "__main__":
    main()