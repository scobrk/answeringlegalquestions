"""
NSW-Specific Legal Document Filtering and Validation
Backend Agent Implementation (KAN-3)
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class NSWLegislationMetadata:
    """Enhanced metadata for NSW legislation"""
    act_name: str
    act_number: Optional[str] = None
    year: Optional[int] = None
    section_number: Optional[str] = None
    subsection: Optional[str] = None
    effective_date: Optional[datetime] = None
    last_amended: Optional[datetime] = None
    keywords: List[str] = field(default_factory=list)
    document_type: str = "legislation"
    jurisdiction: str = "NSW"
    confidence_score: float = 0.0


class NSWRevenueFilter:
    """
    Advanced filtering for NSW Revenue legislation
    Implements sophisticated pattern matching and validation
    """

    def __init__(self):
        # Priority NSW Revenue Acts (from KAN-3)
        self.priority_acts = {
            "duties_act": {
                "names": ["duties act 1997", "stamp duties act"],
                "patterns": [r"duties act \d{4}", r"stamp duties"],
                "topics": ["stamp duty", "duty rates", "conveyance", "transfer duty"]
            },
            "payroll_tax": {
                "names": ["payroll tax act 2007"],
                "patterns": [r"payroll tax act \d{4}"],
                "topics": ["payroll tax", "wages", "employer", "threshold"]
            },
            "land_tax": {
                "names": ["land tax act 1956", "land tax management act 1956"],
                "patterns": [r"land tax.*act \d{4}"],
                "topics": ["land tax", "land value", "property tax", "exemption"]
            },
            "revenue_admin": {
                "names": ["revenue administration act 1996", "taxation administration act"],
                "patterns": [r"revenue administration act \d{4}", r"taxation administration"],
                "topics": ["administration", "assessment", "review", "penalty"]
            },
            "fines": {
                "names": ["fines act", "penalty notices enforcement act"],
                "patterns": [r"fines act \d{4}", r"penalty notices.*act"],
                "topics": ["penalty", "fine", "enforcement", "court"]
            }
        }

        # NSW jurisdiction indicators
        self.nsw_indicators = [
            r"new south wales",
            r"\bnsw\b",
            r"nsw caselaw",
            r"nsw legislation",
            r"supreme court of new south wales",
            r"nsw court",
            r"revenue nsw",
            r"state revenue office"
        ]

        # Section number patterns
        self.section_patterns = [
            r"section\s+(\d+[A-Z]*)",
            r"s\.?\s*(\d+[A-Z]*)",
            r"subsection\s*\(([^)]+)\)",
            r"\((\d+[a-z]*)\)"
        ]

        # Date patterns for amendments
        self.date_patterns = [
            r"(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})",
            r"(\d{4})-(\d{2})-(\d{2})",
            r"(\d{1,2})/(\d{1,2})/(\d{4})"
        ]

    def calculate_nsw_confidence(self, text: str, title: str) -> float:
        """
        Calculate confidence score for NSW jurisdiction

        Args:
            text: Document content
            title: Document title

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.0
        text_lower = text.lower()
        title_lower = title.lower()

        # Check for NSW indicators
        for indicator in self.nsw_indicators:
            if re.search(indicator, text_lower, re.IGNORECASE):
                confidence += 0.2
            if re.search(indicator, title_lower, re.IGNORECASE):
                confidence += 0.3

        # Bonus for Revenue NSW specific terms
        revenue_terms = ["revenue nsw", "state revenue", "revenue office"]
        for term in revenue_terms:
            if term in text_lower:
                confidence += 0.3

        return min(confidence, 1.0)

    def calculate_revenue_confidence(self, text: str, title: str) -> float:
        """
        Calculate confidence score for revenue legislation

        Args:
            text: Document content
            title: Document title

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence = 0.0
        text_lower = text.lower()
        title_lower = title.lower()

        # Check for priority acts
        for act_type, act_info in self.priority_acts.items():
            # Check act names
            for name in act_info["names"]:
                if name in title_lower:
                    confidence += 0.4
                if name in text_lower:
                    confidence += 0.2

            # Check patterns
            for pattern in act_info["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    confidence += 0.2

            # Check topics
            for topic in act_info["topics"]:
                if topic in text_lower:
                    confidence += 0.1

        return min(confidence, 1.0)

    def extract_act_name(self, title: str, text: str) -> Optional[str]:
        """
        Extract standardized act name

        Args:
            title: Document title
            text: Document content

        Returns:
            Standardized act name or None
        """
        title_lower = title.lower()

        for act_type, act_info in self.priority_acts.items():
            for name in act_info["names"]:
                if name in title_lower:
                    # Return standardized name
                    return name.title()

            for pattern in act_info["patterns"]:
                match = re.search(pattern, title_lower, re.IGNORECASE)
                if match:
                    return match.group(0).title()

        return None

    def extract_act_number(self, title: str, text: str) -> Optional[str]:
        """
        Extract act number (e.g., "1997 No 123")

        Args:
            title: Document title
            text: Document content

        Returns:
            Act number or None
        """
        patterns = [
            r"(\d{4})\s+no\.?\s*(\d+)",
            r"act\s+(\d{4})\s+no\.?\s*(\d+)",
            r"(\d{4})\s+act\s+no\.?\s*(\d+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, title.lower())
            if match:
                return f"{match.group(1)} No {match.group(2)}"

        return None

    def extract_sections(self, text: str) -> List[str]:
        """
        Extract section numbers from document

        Args:
            text: Document content

        Returns:
            List of section numbers
        """
        sections = set()

        for pattern in self.section_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                sections.add(match.group(1))

        return sorted(list(sections))

    def extract_keywords(self, text: str, act_type: Optional[str] = None) -> List[str]:
        """
        Extract relevant keywords from text

        Args:
            text: Document content
            act_type: Type of act (optional)

        Returns:
            List of keywords
        """
        keywords = set()
        text_lower = text.lower()

        # General revenue keywords
        general_keywords = [
            "tax", "duty", "assessment", "penalty", "exemption",
            "threshold", "rate", "calculation", "administration",
            "revenue", "payment", "liability", "enforcement"
        ]

        for keyword in general_keywords:
            if keyword in text_lower:
                keywords.add(keyword)

        # Act-specific keywords
        if act_type:
            act_info = self.priority_acts.get(act_type, {})
            for topic in act_info.get("topics", []):
                if topic in text_lower:
                    keywords.add(topic)

        return sorted(list(keywords))

    def extract_dates(self, text: str) -> Dict[str, Optional[datetime]]:
        """
        Extract relevant dates from document

        Args:
            text: Document content

        Returns:
            Dictionary with effective_date and last_amended
        """
        dates = {
            "effective_date": None,
            "last_amended": None
        }

        # Look for amendment dates
        amendment_patterns = [
            r"amended\s+on\s+([^.]+)",
            r"last\s+amended\s+([^.]+)",
            r"as\s+amended\s+([^.]+)"
        ]

        for pattern in amendment_patterns:
            match = re.search(pattern, text.lower())
            if match:
                date_str = match.group(1)
                parsed_date = self.parse_date(date_str)
                if parsed_date:
                    dates["last_amended"] = parsed_date
                    break

        return dates

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse date string to datetime

        Args:
            date_str: Date string

        Returns:
            Parsed datetime or None
        """
        for pattern in self.date_patterns:
            match = re.search(pattern, date_str.lower())
            if match:
                try:
                    if "january" in pattern:
                        # Handle month name format
                        day, month_name, year = match.groups()
                        month_map = {
                            "january": 1, "february": 2, "march": 3, "april": 4,
                            "may": 5, "june": 6, "july": 7, "august": 8,
                            "september": 9, "october": 10, "november": 11, "december": 12
                        }
                        month = month_map.get(month_name)
                        if month:
                            return datetime(int(year), month, int(day))
                    else:
                        # Handle numeric format
                        groups = match.groups()
                        if len(groups) == 3:
                            return datetime(int(groups[2]), int(groups[1]), int(groups[0]))
                except (ValueError, TypeError):
                    continue

        return None

    def filter_and_enhance(self, document: Dict) -> Optional[NSWLegislationMetadata]:
        """
        Filter document and extract enhanced metadata

        Args:
            document: Document dictionary

        Returns:
            NSWLegislationMetadata if document qualifies, None otherwise
        """
        title = str(document.get('title', ''))
        text = str(document.get('text', ''))

        # Calculate confidence scores
        nsw_confidence = self.calculate_nsw_confidence(text, title)
        revenue_confidence = self.calculate_revenue_confidence(text, title)

        # Minimum confidence thresholds
        if nsw_confidence < 0.3 or revenue_confidence < 0.2:
            return None

        # Extract metadata
        act_name = self.extract_act_name(title, text)
        if not act_name:
            return None

        act_number = self.extract_act_number(title, text)
        sections = self.extract_sections(text)
        keywords = self.extract_keywords(text)
        dates = self.extract_dates(text)

        # Calculate combined confidence
        combined_confidence = (nsw_confidence + revenue_confidence) / 2

        metadata = NSWLegislationMetadata(
            act_name=act_name,
            act_number=act_number,
            section_number=sections[0] if sections else None,
            keywords=keywords,
            effective_date=dates.get("effective_date"),
            last_amended=dates.get("last_amended"),
            confidence_score=combined_confidence
        )

        logger.info(f"Filtered document: {act_name} (confidence: {combined_confidence:.2f})")

        return metadata

    def validate_document_quality(self, text: str, metadata: NSWLegislationMetadata) -> bool:
        """
        Validate document quality for processing

        Args:
            text: Document content
            metadata: Document metadata

        Returns:
            True if document meets quality standards
        """
        # Minimum content length
        if len(text) < 500:
            logger.warning(f"Document too short: {len(text)} characters")
            return False

        # Must have act name
        if not metadata.act_name:
            logger.warning("Missing act name")
            return False

        # Minimum confidence threshold
        if metadata.confidence_score < 0.4:
            logger.warning(f"Low confidence score: {metadata.confidence_score}")
            return False

        return True


def main():
    """Test the NSW filter"""
    filter_engine = NSWRevenueFilter()

    # Test document
    test_doc = {
        'title': 'Duties Act 1997 No 123 NSW',
        'text': '''
        This is the Duties Act 1997 of New South Wales.
        Section 31 provides for stamp duty on conveyances.
        The current rate is 5.5% for properties over $1 million.
        This act was last amended on 15 March 2023.
        '''
    }

    result = filter_engine.filter_and_enhance(test_doc)
    if result:
        print(f"Act Name: {result.act_name}")
        print(f"Act Number: {result.act_number}")
        print(f"Keywords: {result.keywords}")
        print(f"Confidence: {result.confidence_score}")
        print(f"Last Amended: {result.last_amended}")
    else:
        print("Document did not pass filter")


if __name__ == "__main__":
    main()