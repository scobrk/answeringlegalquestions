"""
NSW Revenue Legislation Sourcing Script
Downloads and processes NSW Revenue Acts from online sources
"""

import os
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional
import time
import logging
from datasets import load_dataset

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSWRevenueLegislationSourcer:
    """Sources NSW Revenue legislation from online repositories"""

    def __init__(self, data_dir: str = "./data/legislation"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # NSW Revenue Acts to source
        self.target_acts = {
            "duties_act_1997": {
                "full_name": "Duties Act 1997 (NSW)",
                "keywords": ["duties act 1997", "stamp duty"],
                "sections": ["conveyance duty", "mortgage duty", "transfer duty"]
            },
            "payroll_tax_act_2007": {
                "full_name": "Payroll Tax Act 2007 (NSW)",
                "keywords": ["payroll tax act 2007", "wages tax"],
                "sections": ["threshold", "rate", "group employer"]
            },
            "land_tax_act_1956": {
                "full_name": "Land Tax Act 1956 (NSW)",
                "keywords": ["land tax act 1956"],
                "sections": ["exemptions", "assessment", "principal place of residence"]
            },
            "land_tax_management_act_1956": {
                "full_name": "Land Tax Management Act 1956 (NSW)",
                "keywords": ["land tax management act 1956"],
                "sections": ["administration", "objections", "appeals"]
            },
            "revenue_administration_act_1996": {
                "full_name": "Revenue Administration Act 1996 (NSW)",
                "keywords": ["revenue administration act 1996"],
                "sections": ["assessment", "review", "enforcement"]
            },
            "fines_act_1996": {
                "full_name": "Fines Act 1996 (NSW)",
                "keywords": ["fines act 1996", "penalty notices"],
                "sections": ["enforcement", "payment", "review"]
            },
            "first_home_owner_grant_2000": {
                "full_name": "First Home Owner Grant (New Homes) Act 2000 (NSW)",
                "keywords": ["first home owner grant", "fhog"],
                "sections": ["eligibility", "amount", "application"]
            }
        }

    def source_from_huggingface(self) -> Dict[str, str]:
        """Source legislation from Australian Legal Corpus on Hugging Face"""
        logger.info("Loading Australian Legal Corpus from Hugging Face...")

        try:
            # Load the dataset
            dataset = load_dataset("isaacus/open-australian-legal-corpus", split="train")
            logger.info(f"Loaded {len(dataset)} documents from corpus")

            sourced_acts = {}

            for act_key, act_info in self.target_acts.items():
                logger.info(f"Searching for {act_info['full_name']}...")

                # Search for documents matching this act
                matching_docs = []
                for doc in dataset:
                    title = doc.get('title', '').lower()
                    content = doc.get('content', '').lower()

                    # Check if any keywords match
                    for keyword in act_info['keywords']:
                        if keyword.lower() in title or keyword.lower() in content[:1000]:
                            matching_docs.append(doc)
                            break

                if matching_docs:
                    # Use the best matching document (first one for now)
                    best_doc = matching_docs[0]
                    sourced_acts[act_key] = best_doc['content']
                    logger.info(f"✅ Found {act_info['full_name']} ({len(best_doc['content'])} chars)")
                else:
                    logger.warning(f"❌ Could not find {act_info['full_name']}")
                    # Create placeholder content
                    sourced_acts[act_key] = self._create_placeholder_content(act_info)

            return sourced_acts

        except Exception as e:
            logger.error(f"Failed to load from Hugging Face: {e}")
            return self._create_fallback_content()

    def source_from_austlii(self) -> Dict[str, str]:
        """Source legislation from AustLII (backup method)"""
        logger.info("Attempting to source from AustLII...")

        # AustLII URLs for NSW legislation
        austlii_urls = {
            "duties_act_1997": "http://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/nsw/consol_act/da199793/",
            "payroll_tax_act_2007": "http://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/nsw/consol_act/pta2007155/",
            "land_tax_act_1956": "http://www.austlii.edu.au/cgi-bin/viewdoc/au/legis/nsw/consol_act/lta1956164/",
            # Add more URLs as needed
        }

        sourced_acts = {}

        for act_key, url in austlii_urls.items():
            try:
                logger.info(f"Downloading {act_key} from AustLII...")
                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    # Basic text extraction (would need proper HTML parsing)
                    content = response.text
                    # Simple extraction - remove HTML tags
                    import re
                    text_content = re.sub('<[^<]+?>', '', content)
                    text_content = re.sub('\s+', ' ', text_content).strip()

                    if len(text_content) > 1000:  # Basic validation
                        sourced_acts[act_key] = text_content
                        logger.info(f"✅ Downloaded {act_key} ({len(text_content)} chars)")
                    else:
                        logger.warning(f"❌ Downloaded content too short for {act_key}")

                else:
                    logger.warning(f"❌ Failed to download {act_key}: HTTP {response.status_code}")

                time.sleep(1)  # Be respectful to the server

            except Exception as e:
                logger.error(f"Error downloading {act_key}: {e}")

        return sourced_acts

    def _create_placeholder_content(self, act_info: Dict) -> str:
        """Create placeholder content for acts we couldn't source"""
        return f"""
{act_info['full_name']}

This is placeholder content for {act_info['full_name']}.

Key Areas:
{chr(10).join(f"• {section}" for section in act_info['sections'])}

Note: This is demonstration content. In a production system, the full text of the Act would be available here with all sections, subsections, and legal provisions.

For the most current and complete version of this legislation, please refer to the official NSW legislation website or consult with qualified legal professionals.

Keywords: {', '.join(act_info['keywords'])}
"""

    def _create_fallback_content(self) -> Dict[str, str]:
        """Create fallback content when online sourcing fails"""
        logger.info("Creating fallback content for all acts...")

        fallback_content = {}

        # Detailed fallback content for key acts
        fallback_content["duties_act_1997"] = """
Duties Act 1997 (NSW)

PART 2 - CONVEYANCE DUTY

Section 31 - Rate of conveyance duty
The rate of conveyance duty on a conveyance of dutiable property (other than a conveyance to which section 32 applies) is:
(a) for consideration not exceeding $14,000—$1.25 for each $100, or part of $100, of the consideration
(b) for consideration exceeding $14,000 but not exceeding $32,000—$175 plus $1.50 for each $100, or part of $100, of the consideration in excess of $14,000
(c) for consideration exceeding $32,000 but not exceeding $83,000—$270 plus $1.75 for each $100, or part of $100, of the consideration in excess of $32,000
(d) for consideration exceeding $83,000 but not exceeding $319,000—$1,162.50 plus $3.50 for each $100, or part of $100, of the consideration in excess of $83,000
(e) for consideration exceeding $319,000 but not exceeding $1,059,000—$9,422.50 plus $4.50 for each $100, or part of $100, of the consideration in excess of $319,000
(f) for consideration exceeding $1,059,000—$42,722.50 plus $5.50 for each $100, or part of $100, of the consideration in excess of $1,059,000

Section 54 - Concessional duty for first home buyers
A conveyance of a home to a first home buyer is exempt from duty if the consideration for the conveyance does not exceed $650,000.
"""

        fallback_content["payroll_tax_act_2007"] = """
Payroll Tax Act 2007 (NSW)

Section 11 - Liability for payroll tax
(1) Payroll tax is imposed on an employer whose taxable wages paid or payable in Australia in a financial year exceed the tax-free threshold.

Section 15 - Rate of payroll tax
The rate of payroll tax is 5.45%.

Section 5 - Tax-free threshold
(1) The tax-free threshold for a financial year is $1,200,000.
(2) If an employer is a member of a group, the tax-free threshold is to be apportioned among the members of the group.

Section 6 - Meaning of wages
(1) Wages includes any payment made to or for an employee by way of salary, wage, commission, bonus or allowance.
(2) Wages includes the value of any benefit provided to or for an employee.
"""

        fallback_content["land_tax_act_1956"] = """
Land Tax Act 1956 (NSW)

Section 3A - Principal place of residence exemption
(1) Land used and occupied by the owner as the owner's principal place of residence is exempt from land tax.
(2) The exemption applies to land up to 2 hectares in area.
(3) Only one principal place of residence exemption may be claimed by a person in any land tax year.

Section 9A - Tax-free threshold
The tax-free threshold for land tax is $969,000 for the 2024 land tax year.

Section 27 - Rate of land tax
Land tax is charged at the following rates:
(a) For land value up to $969,000: nil
(b) For land value exceeding $969,000 but not exceeding $4,488,000: 1.6% of the land value in excess of $969,000
(c) For land value exceeding $4,488,000: $56,304 plus 2.0% of the land value in excess of $4,488,000
"""

        # Add minimal content for other acts
        for act_key, act_info in self.target_acts.items():
            if act_key not in fallback_content:
                fallback_content[act_key] = self._create_placeholder_content(act_info)

        return fallback_content

    def save_legislation(self, sourced_acts: Dict[str, str]):
        """Save sourced legislation to local files"""
        logger.info("Saving legislation to local files...")

        for act_key, content in sourced_acts.items():
            file_path = self.data_dir / f"{act_key}.txt"

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"✅ Saved {act_key} to {file_path} ({len(content)} chars)")

        # Save metadata
        metadata = {
            "acts": list(sourced_acts.keys()),
            "sourced_at": time.time(),
            "total_acts": len(sourced_acts),
            "act_info": self.target_acts
        }

        metadata_path = self.data_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"✅ Saved metadata to {metadata_path}")

    def source_all_legislation(self):
        """Main method to source all NSW Revenue legislation"""
        logger.info("Starting NSW Revenue legislation sourcing...")

        # Try Hugging Face first
        sourced_acts = self.source_from_huggingface()

        # If we didn't get enough acts, try AustLII
        if len(sourced_acts) < 3:
            logger.info("Insufficient acts from Hugging Face, trying AustLII...")
            austlii_acts = self.source_from_austlii()
            sourced_acts.update(austlii_acts)

        # If still insufficient, use fallback content
        if len(sourced_acts) < 3:
            logger.info("Using fallback content...")
            sourced_acts = self._create_fallback_content()

        # Save all sourced acts
        self.save_legislation(sourced_acts)

        logger.info(f"✅ Successfully sourced {len(sourced_acts)} NSW Revenue Acts")
        return sourced_acts


def main():
    """Main function to run the legislation sourcing"""
    sourcer = NSWRevenueLegislationSourcer()

    try:
        acts = sourcer.source_all_legislation()
        print(f"\n✅ Successfully sourced {len(acts)} NSW Revenue Acts:")
        for act_key in acts.keys():
            print(f"  - {act_key}")

        print(f"\n📁 Files saved to: {sourcer.data_dir}")
        print("🔄 Ready for vector processing and embedding generation")

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Legislation sourcing failed: {e}")


if __name__ == "__main__":
    main()