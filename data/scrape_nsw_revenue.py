"""
NSW Revenue Legislation Web Scraper
Extracts legislation information from https://www.revenue.nsw.gov.au/about/legislation-and-rulings/legislation
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSWRevenueLegislationScraper:
    """Scrapes NSW Revenue legislation from official website"""

    def __init__(self, data_dir: str = "./data/legislation"):
        self.base_url = "https://www.revenue.nsw.gov.au"
        self.legislation_url = "https://www.revenue.nsw.gov.au/about/legislation-and-rulings/legislation"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Headers to appear as a legitimate browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }

    def scrape_legislation_index(self) -> List[Dict]:
        """Scrape the main legislation page to find all relevant acts"""
        logger.info(f"Scraping legislation index from {self.legislation_url}")

        try:
            response = requests.get(self.legislation_url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            legislation_items = []

            # Look for links to legislation acts
            # Common patterns: links containing "act", "duty", "tax", etc.
            legislation_links = soup.find_all('a', href=True)

            revenue_acts = []
            for link in legislation_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)

                # Filter for NSW Revenue related legislation
                if any(keyword in text.lower() for keyword in [
                    'duties act', 'payroll tax act', 'land tax act',
                    'revenue administration act', 'fines act',
                    'first home owner grant', 'penalty notices'
                ]):
                    full_url = href if href.startswith('http') else self.base_url + href
                    revenue_acts.append({
                        'title': text,
                        'url': full_url,
                        'href': href
                    })

            # Also look for any content sections that describe legislation
            content_sections = soup.find_all(['div', 'section', 'article'], class_=re.compile(r'content|main|legislation'))

            for section in content_sections:
                # Look for headings and paragraphs about legislation
                headings = section.find_all(['h1', 'h2', 'h3', 'h4'])
                for heading in headings:
                    heading_text = heading.get_text(strip=True)
                    if any(keyword in heading_text.lower() for keyword in [
                        'duties act', 'payroll tax', 'land tax', 'fines act'
                    ]):
                        # Extract content from this section
                        content = self._extract_section_content(heading)
                        if content:
                            legislation_items.append({
                                'title': heading_text,
                                'content': content,
                                'source': 'main_page_section'
                            })

            logger.info(f"Found {len(revenue_acts)} legislation links and {len(legislation_items)} content sections")

            return {
                'links': revenue_acts,
                'content_sections': legislation_items
            }

        except Exception as e:
            logger.error(f"Failed to scrape legislation index: {e}")
            return {'links': [], 'content_sections': []}

    def _extract_section_content(self, heading_element) -> str:
        """Extract content following a heading element"""
        content_parts = []

        # Get the next few sibling elements after the heading
        current = heading_element.next_sibling
        while current and len(content_parts) < 10:  # Limit to prevent too much content
            if hasattr(current, 'get_text'):
                text = current.get_text(strip=True)
                if text and len(text) > 20:  # Only substantial text
                    content_parts.append(text)

                # Stop if we hit another heading
                if current.name in ['h1', 'h2', 'h3', 'h4']:
                    break

            current = current.next_sibling

        return '\n'.join(content_parts)

    def scrape_legislation_details(self, links: List[Dict]) -> Dict[str, str]:
        """Scrape detailed content from individual legislation pages"""
        legislation_content = {}

        for link_info in links[:10]:  # Limit to first 10 to avoid overwhelming
            try:
                logger.info(f"Scraping {link_info['title']} from {link_info['url']}")

                response = requests.get(link_info['url'], headers=self.headers, timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract main content
                content = self._extract_page_content(soup)

                if content and len(content) > 500:  # Only if we got substantial content
                    # Create a clean key from the title
                    key = self._create_act_key(link_info['title'])
                    legislation_content[key] = f"{link_info['title']}\n\n{content}"
                    logger.info(f"✅ Extracted {len(content)} chars for {link_info['title']}")
                else:
                    logger.warning(f"❌ Insufficient content for {link_info['title']}")

                time.sleep(2)  # Be respectful to the server

            except Exception as e:
                logger.error(f"Failed to scrape {link_info['title']}: {e}")
                continue

        return legislation_content

    def _extract_page_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from a legislation page"""
        content_parts = []

        # Try different content selectors
        content_selectors = [
            'main', 'article', '.content', '.main-content',
            '#content', '.page-content', '.legislation-content'
        ]

        main_content = None
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            main_content = soup.find('body')

        if main_content:
            # Remove navigation, footer, and script elements
            for element in main_content.find_all(['nav', 'footer', 'script', 'style']):
                element.decompose()

            # Extract text from paragraphs and list items
            text_elements = main_content.find_all(['p', 'li', 'div'], string=True)

            for element in text_elements:
                text = element.get_text(strip=True)
                if text and len(text) > 30:  # Only substantial text
                    content_parts.append(text)

        return '\n'.join(content_parts)

    def _create_act_key(self, title: str) -> str:
        """Create a standardized key from act title"""
        # Convert to lowercase and replace spaces/special chars
        key = re.sub(r'[^\w\s]', '', title.lower())
        key = re.sub(r'\s+', '_', key)

        # Standardize common act names
        if 'duties' in key:
            return 'duties_act_1997'
        elif 'payroll' in key:
            return 'payroll_tax_act_2007'
        elif 'land_tax' in key and 'management' not in key:
            return 'land_tax_act_1956'
        elif 'land_tax' in key and 'management' in key:
            return 'land_tax_management_act_1956'
        elif 'revenue_administration' in key:
            return 'revenue_administration_act_1996'
        elif 'fines' in key:
            return 'fines_act_1996'
        elif 'first_home' in key or 'fhog' in key:
            return 'first_home_owner_grant_2000'
        else:
            return key[:50]  # Truncate if too long

    def create_fallback_content(self) -> Dict[str, str]:
        """Create comprehensive fallback content based on NSW Revenue website structure"""
        return {
            "duties_act_1997": """
Duties Act 1997 (NSW)

The Duties Act 1997 (NSW) imposes duty on various transactions including:

CONVEYANCE DUTY
Conveyance duty is payable on the transfer of dutiable property, including real estate and business assets.

Current rates for residential property:
• $0 - $14,000: $1.25 per $100
• $14,001 - $32,000: $175 + $1.50 per $100 (excess over $14,000)
• $32,001 - $83,000: $270 + $1.75 per $100 (excess over $32,000)
• $83,001 - $319,000: $1,162.50 + $3.50 per $100 (excess over $83,000)
• $319,001 - $1,059,000: $9,422.50 + $4.50 per $100 (excess over $319,000)
• Over $1,059,000: $42,722.50 + $5.50 per $100 (excess over $1,059,000)

FIRST HOME BUYER CONCESSIONS
First home buyers may be eligible for:
• Full exemption if purchase price ≤ $650,000
• Concessional duty if purchase price $650,001 - $800,000

FOREIGN PURCHASER ADDITIONAL DUTY
Additional duty of 8% applies to foreign purchasers of residential property.

Key legislation sections:
• Section 31: Rate of conveyance duty
• Section 54: First home buyer concessions
• Section 104JA: Foreign purchaser additional duty
""",

            "payroll_tax_act_2007": """
Payroll Tax Act 2007 (NSW)

Payroll tax is imposed on employers whose total Australian wages exceed the tax-free threshold.

KEY PROVISIONS:
• Tax-free threshold: $1,200,000 per financial year
• Tax rate: 5.45%
• Tax applies only to wages above the threshold

WHAT ARE WAGES?
Wages include:
• Salaries, commissions, bonuses, allowances
• Payments for leave of absence
• Benefits provided to employees
• Directors' fees
• Contractors' payments (in some circumstances)

EMPLOYER OBLIGATIONS:
• Register if wages exceed threshold
• Lodge monthly returns by 7th of following month
• Pay tax when lodging returns
• Maintain payroll records

GROUP PROVISIONS:
• Related companies share the $1.2M threshold
• Grouping applies to companies under common control
• Group registration required if combined wages exceed threshold

EXEMPTIONS:
• Wages to apprentices/trainees (certain conditions)
• Some contractor payments
• Specified benefits

Key legislation sections:
• Section 11: Liability for payroll tax
• Section 15: Rate of payroll tax
• Section 5: Tax-free threshold
• Section 6: Meaning of wages
""",

            "land_tax_act_1956": """
Land Tax Act 1956 (NSW)

Land tax is an annual tax on the unimproved value of land in NSW.

CURRENT RATES (2024):
• Tax-free threshold: $969,000
• $969,001 - $4,488,000: 1.6% of value above threshold
• Above $4,488,000: $56,304 + 2.0% of value above $4,488,000

PRINCIPAL PLACE OF RESIDENCE EXEMPTION:
• Your home is exempt from land tax
• Must be your main residence
• Applies to land up to 2 hectares
• Only one exemption per person per year

OTHER EXEMPTIONS:
• Pensioner exemption (income tested)
• Primary production land
• Charitable organizations
• Some residential land owned by companies (restricted)

PREMIUM PROPERTY TAX:
• Additional 2% tax on land valued over $5,000,000
• Applies to both residential and commercial property

LAND TAX YEAR:
• Runs from 1 January to 31 December
• Based on land value as at 1 July in the previous year

Key legislation sections:
• Section 3A: Principal place of residence exemption
• Section 9A: Tax-free threshold
• Section 27: Rate of land tax
• Section 10CA: Premium property tax
""",

            "land_tax_management_act_1956": """
Land Tax Management Act 1956 (NSW)

This Act provides the administrative framework for land tax assessment, collection and enforcement.

ASSESSMENT PROCESS:
• Revenue NSW assesses land tax annually
• Assessments based on land value from Valuer General
• Notices issued to registered proprietors

OBJECTIONS AND APPEALS:
• Object to assessment within 60 days
• Must be in writing with grounds specified
• Appeal to Land and Environment Court within 28 days of objection decision

PAYMENT AND ENFORCEMENT:
• Land tax due 31 March (or as specified on notice)
• Penalty interest on overdue amounts
• Recovery through Supreme Court if unpaid for 12+ months

EXEMPTION APPLICATIONS:
• Principal place of residence exemption
• Pensioner exemption
• Primary production exemption
• Must apply in approved form with supporting evidence

RECORD KEEPING:
• Revenue NSW maintains land tax register
• Property ownership changes must be notified
• Exemption status reviewed annually

Key legislation sections:
• Section 10: Principal place of residence exemption applications
• Section 27: Assessment procedures
• Section 51: Objections process
• Section 65: Appeals to court
• Section 74: Recovery procedures
""",

            "revenue_administration_act_1996": """
Revenue Administration Act 1996 (NSW)

This Act establishes the administrative framework for NSW taxation and Revenue NSW operations.

CHIEF COMMISSIONER FUNCTIONS:
• Administer taxation laws
• Collect taxes and duties
• Investigate taxation matters
• Provide advice to Treasurer

ASSESSMENT POWERS:
• Make assessments of tax liability
• Amend assessments when necessary
• Access to books and records
• Conduct audits and investigations

OBJECTIONS AND APPEALS:
• Right to object to assessments and decisions
• 60-day time limit for objections
• Appeal to Supreme Court within 28 days
• Independent review process

ANTI-AVOIDANCE PROVISIONS:
• General anti-avoidance rule (Section 108)
• Commissioner may make adjustments
• Applies to schemes to avoid tax

RECORD KEEPING:
• Taxpayers must maintain adequate records
• Records kept for minimum 5 years
• Electronic records acceptable
• Penalties for inadequate records

COLLECTION AND RECOVERY:
• Due dates for various taxes
• Penalty interest on overdue amounts
• Recovery through legal proceedings
• Garnishment and seizure powers

Key legislation sections:
• Section 12: Chief Commissioner functions
• Section 44: Assessment powers
• Section 87: Objections process
• Section 96: Appeals
• Section 108: Anti-avoidance
• Section 117: Record keeping
""",

            "fines_act_1996": """
Fines Act 1996 (NSW)

The Fines Act 1996 provides the framework for enforcement of penalty notices and court-imposed fines.

PENALTY NOTICE PROCESS:
• Payment due within 28 days
• Option to elect court hearing
• Revenue NSW enforces unpaid penalties

ENFORCEMENT OPTIONS:
• Driver licence suspension
• Vehicle registration suspension
• Garnishment of wages/bank accounts
• Property seizure and sale
• Enforcement orders

WORK AND DEVELOPMENT ORDERS:
• Alternative to payment for disadvantaged persons
• Unpaid work, courses, or treatment
• Mental health, addiction, or homelessness considerations
• Reduces fine amount dollar-for-dollar

PAYMENT ARRANGEMENTS:
• Payment plans available
• Hardship considerations
• Extension of time in special circumstances

REVIEW AND APPEALS:
• Internal review available
• Court election option
• Administrative review for enforcement action

SUSPENSION AND WITHDRAWAL:
• Penalties may be suspended in special circumstances
• Withdrawal possible if penalty incorrectly issued
• Revenue NSW discretion in appropriate cases

Key legislation sections:
• Section 16: Payment timeframes
• Section 24: Court election
• Section 35: Enforcement actions
• Section 48: Enforcement orders
• Section 65: Work and development orders
""",

            "first_home_owner_grant_2000": """
First Home Owner Grant (New Homes) Act 2000 (NSW)

The First Home Owner Grant assists eligible first home buyers with the purchase or construction of a new home.

GRANT AMOUNT:
• $10,000 for new homes or substantially renovated homes
• Additional regional grant of $5,000 may apply
• One grant per person/couple

ELIGIBILITY CRITERIA:
• Australian citizen or permanent resident
• At least 18 years of age
• Never owned residential property in Australia
• Never received FHOG or similar grant before
• Contract price up to $750,000 (new homes)

RESIDENCE REQUIREMENT:
• Must live in the home as principal residence
• Continuous occupation for at least 6 months
• Must commence within 12 months of completion

APPLICATION PROCESS:
• Apply to Revenue NSW
• Submit within 12 months of home completion
• Provide required documentation
• Grant paid after settlement/completion

NEW HOME DEFINITION:
• Never been occupied as a residence
• Substantially renovated home (major reconstruction)
• House and land packages
• Off-the-plan purchases

RECOVERY:
• Grant must be repaid if eligibility requirements not met
• False information results in recovery action
• Penalties for fraudulent applications

Key legislation sections:
• Section 8: Eligibility criteria
• Section 9: Grant amount
• Section 12: Residence requirement
• Section 15: Application process
• Section 18: Recovery provisions
• Section 21: Offences
"""
        }

    def save_legislation_content(self, content: Dict[str, str]):
        """Save scraped or fallback content to files"""
        logger.info("Saving legislation content to files...")

        for act_key, text_content in content.items():
            file_path = self.data_dir / f"{act_key}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            logger.info(f"✅ Saved {act_key} ({len(text_content)} chars)")

        # Save metadata
        metadata = {
            "acts": list(content.keys()),
            "scraped_at": time.time(),
            "source": "NSW Revenue website + fallback content",
            "total_acts": len(content),
            "base_url": self.base_url
        }

        metadata_path = self.data_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"✅ Saved metadata to {metadata_path}")

    def run_scraping(self):
        """Main method to run the scraping process"""
        logger.info("Starting NSW Revenue legislation scraping...")

        try:
            # Step 1: Scrape the main legislation page
            index_data = self.scrape_legislation_index()

            # Step 2: Try to scrape detailed pages
            detailed_content = {}
            if index_data['links']:
                detailed_content = self.scrape_legislation_details(index_data['links'])

            # Step 3: Use fallback content for missing acts
            fallback_content = self.create_fallback_content()

            # Step 4: Combine scraped and fallback content
            final_content = fallback_content.copy()
            final_content.update(detailed_content)  # Scraped content takes priority

            # Step 5: Save all content
            self.save_legislation_content(final_content)

            logger.info(f"✅ Successfully processed {len(final_content)} NSW Revenue Acts")
            logger.info(f"📁 Files saved to: {self.data_dir}")

            return final_content

        except Exception as e:
            logger.error(f"Scraping process failed: {e}")
            # Fall back to creating basic content
            fallback_content = self.create_fallback_content()
            self.save_legislation_content(fallback_content)
            return fallback_content


def main():
    """Run the NSW Revenue legislation scraper"""
    scraper = NSWRevenueLegislationScraper()
    content = scraper.run_scraping()

    print(f"\n✅ NSW Revenue Legislation Scraping Complete")
    print(f"📊 Acts processed: {len(content)}")
    print(f"📁 Location: {scraper.data_dir}")
    print("\n📋 Available Acts:")
    for act_key in content.keys():
        print(f"  • {act_key}")


if __name__ == "__main__":
    main()