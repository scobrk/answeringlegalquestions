"""
Targeted Sourcing Agent for NSW Revenue AI Assistant
Uses classification results to retrieve specific, relevant sources
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

from openai import OpenAI
from dotenv import load_dotenv

# Optional import for datasets - graceful fallback for Render deployment
try:
    from datasets import load_dataset
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False
    def load_dataset(*args, **kwargs):
        raise ImportError("datasets package not available in this deployment")

import sys
from pathlib import Path

# Add project root to path to ensure imports work
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

try:
    from agents.classification_agent import ClassificationResult, RevenueType, QuestionIntent
except ImportError:
    try:
        from .classification_agent import ClassificationResult, RevenueType, QuestionIntent
    except ImportError:
        from classification_agent import ClassificationResult, RevenueType, QuestionIntent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SourcedContent:
    """Content with source attribution and highlighting"""
    id: str
    title: str
    content: str
    source_type: str  # 'legislation', 'website', 'huggingface'
    url: Optional[str] = None
    relevance_score: float = 0.0
    highlighted_text: List[str] = None  # Specific text passages used
    section: Optional[str] = None
    act_name: Optional[str] = None


class TargetedSourcingAgent:
    """
    Retrieves targeted sources based on classification results
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Source mappings based on revenue type
        self.revenue_source_mapping = {
            RevenueType.PAYROLL_TAX: {
                'legislation': ['payroll_tax_act', 'payroll_tax_regulation'],
                'website_paths': ['/taxes-and-duties/payroll-tax', '/help-and-support/payroll-tax'],
                'keywords': ['payroll tax', 'employer', 'wages', 'threshold', 'exemption']
            },
            RevenueType.LAND_TAX: {
                'legislation': ['land_tax_management_act', 'land_tax_regulation'],
                'website_paths': ['/taxes-and-duties/land-tax', '/help-and-support/land-tax'],
                'keywords': ['land tax', 'property', 'unimproved value', 'exemption', 'threshold']
            },
            RevenueType.STAMP_DUTY: {
                'legislation': ['duties_act', 'stamp_duties_regulation'],
                'website_paths': ['/taxes-and-duties/transfer-duty', '/help-and-support/transfer-duty'],
                'keywords': ['stamp duty', 'conveyance duty', 'transfer duty', 'first home buyer']
            },
            RevenueType.REVENUE_ADMINISTRATION: {
                'legislation': ['taxation_administration_act', 'revenue_administration_regulation'],
                'website_paths': ['/about/legislation-and-rulings', '/help-and-support/objections'],
                'keywords': ['objection', 'appeal', 'assessment', 'penalty', 'compliance']
            }
        }

        # Intent-specific source requirements
        self.intent_source_requirements = {
            QuestionIntent.CALCULATION: ['rates', 'thresholds', 'calculation_examples'],
            QuestionIntent.ELIGIBILITY: ['exemptions', 'eligibility_criteria', 'concessions'],
            QuestionIntent.PROCESS: ['procedures', 'forms', 'application_process'],
            QuestionIntent.DEADLINE: ['due_dates', 'payment_schedules', 'deadlines'],
            QuestionIntent.PENALTY: ['penalty_provisions', 'enforcement', 'interest_rates']
        }

        # NSW Revenue base URLs
        self.nsw_revenue_base = "https://www.revenue.nsw.gov.au"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def get_targeted_sources(self, question: str, classification: ClassificationResult,
                           max_sources: int = 8) -> List[SourcedContent]:
        """
        Get targeted sources based on classification results

        Args:
            question: Original question
            classification: Classification result from classification agent
            max_sources: Maximum number of sources to return

        Returns:
            List of SourcedContent objects with targeted, relevant sources
        """
        # Check if this is a multi-tax scenario
        if hasattr(classification, 'requires_multi_tax_analysis') and classification.requires_multi_tax_analysis:
            logger.info(f"Getting sources for multi-tax scenario: {[rt.value for rt in classification.all_revenue_types]}")
        else:
            logger.info(f"Getting targeted sources for {classification.revenue_type.value} "
                       f"with intent {classification.question_intent.value}")

        sources = []

        # Parallel source retrieval based on classification
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit targeted retrieval tasks - handle multi-tax scenarios
            legislation_future = executor.submit(
                self._get_multi_tax_legislation, classification
            )
            website_future = executor.submit(
                self._get_targeted_website_content, classification
            )
            corpus_future = executor.submit(
                self._get_targeted_corpus_content, classification
            )

            # Collect results
            try:
                legislation_sources = legislation_future.result(timeout=15)
                sources.extend(legislation_sources)
                logger.info(f"Retrieved {len(legislation_sources)} legislation sources")
            except Exception as e:
                logger.warning(f"Legislation retrieval failed: {e}")

            try:
                website_sources = website_future.result(timeout=20)
                sources.extend(website_sources)
                logger.info(f"Retrieved {len(website_sources)} website sources")
            except Exception as e:
                logger.warning(f"Website retrieval failed: {e}")

            try:
                corpus_sources = corpus_future.result(timeout=25)
                sources.extend(corpus_sources)
                logger.info(f"Retrieved {len(corpus_sources)} corpus sources")
            except Exception as e:
                logger.warning(f"Corpus retrieval failed: {e}")

        # Rank sources by relevance to the specific question and classification
        ranked_sources = self._rank_sources_by_classification(question, classification, sources)

        # Highlight specific text passages that will be used in the answer
        highlighted_sources = self._highlight_relevant_passages(question, ranked_sources[:max_sources])

        return highlighted_sources

    def _get_multi_tax_legislation(self, classification: ClassificationResult) -> List[SourcedContent]:
        """Get legislation sources for all applicable tax types"""
        sources = []

        # Get all revenue types to source
        if hasattr(classification, 'all_revenue_types') and classification.all_revenue_types:
            revenue_types = classification.all_revenue_types
        else:
            revenue_types = [classification.revenue_type]

        # Create modified classification for each tax type
        for revenue_type in revenue_types:
            temp_classification = type(classification)(
                revenue_type=revenue_type,
                question_intent=classification.question_intent,
                confidence=classification.confidence,
                key_entities=classification.key_entities,
                source_requirements=classification.source_requirements,
                search_terms=classification.search_terms,
                all_revenue_types=getattr(classification, 'all_revenue_types', [revenue_type]),
                requires_multi_tax_analysis=getattr(classification, 'requires_multi_tax_analysis', False),
                is_simple_calculation=getattr(classification, 'is_simple_calculation', False)
            )

            # Get legislation for this specific tax type
            tax_sources = self._get_targeted_legislation(temp_classification)
            sources.extend(tax_sources)

        return sources

    def _get_targeted_legislation(self, classification: ClassificationResult) -> List[SourcedContent]:
        """Get targeted legislation sources based on revenue type"""
        sources = []

        if classification.revenue_type not in self.revenue_source_mapping:
            return sources

        mapping = self.revenue_source_mapping[classification.revenue_type]

        from pathlib import Path
        legislation_dir = Path("./data/legislation")

        if not legislation_dir.exists():
            logger.warning("Legislation directory not found")
            return sources

        # Get all legislation files and filter by relevance to revenue type
        for txt_file in legislation_dir.glob("*.txt"):
            if txt_file.name == "metadata.json":
                continue

            # Check if filename is relevant to the revenue type
            filename_lower = txt_file.stem.lower()
            is_relevant = False

            if classification.revenue_type == RevenueType.PAYROLL_TAX:
                is_relevant = 'payroll' in filename_lower
            elif classification.revenue_type == RevenueType.LAND_TAX:
                is_relevant = 'land_tax' in filename_lower
            elif classification.revenue_type == RevenueType.STAMP_DUTY:
                is_relevant = 'duties' in filename_lower or 'stamp' in filename_lower
            elif classification.revenue_type == RevenueType.REVENUE_ADMINISTRATION:
                is_relevant = 'administration' in filename_lower or 'revenue' in filename_lower

            if is_relevant:
                try:
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Filter content based on search terms and intent
                    relevant_sections = self._extract_relevant_sections(
                        content, classification.search_terms, classification.question_intent
                    )

                    if relevant_sections:
                        source = SourcedContent(
                            id=f"legislation_{txt_file.stem}",
                            title=txt_file.stem.replace('_', ' ').title(),
                            content=relevant_sections,
                            source_type='legislation',
                            act_name=txt_file.stem,
                            relevance_score=self._calculate_legislation_relevance(
                                relevant_sections, classification
                            )
                        )
                        sources.append(source)

                except Exception as e:
                    logger.warning(f"Failed to read {txt_file}: {e}")

        return sources

    def _get_targeted_website_content(self, classification: ClassificationResult) -> List[SourcedContent]:
        """Get targeted NSW Revenue website content"""
        sources = []

        if classification.revenue_type not in self.revenue_source_mapping:
            return sources

        mapping = self.revenue_source_mapping[classification.revenue_type]
        website_paths = mapping.get('website_paths', [])

        for path in website_paths:
            try:
                url = f"{self.nsw_revenue_base}{path}"
                response = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract main content
                content_div = soup.find('div', class_=['content', 'main-content', 'article'])
                if content_div:
                    content = content_div.get_text(strip=True)

                    # Filter content based on classification
                    if self._is_content_relevant(content, classification):
                        relevant_text = self._extract_relevant_text(content, classification)

                        source = SourcedContent(
                            id=f"website_{hash(url)}",
                            title=self._extract_page_title(soup),
                            content=relevant_text,
                            source_type='website',
                            url=url,
                            relevance_score=self._calculate_website_relevance(
                                relevant_text, classification
                            )
                        )
                        sources.append(source)

            except Exception as e:
                logger.warning(f"Failed to fetch website content from {path}: {e}")

        return sources

    def _get_targeted_corpus_content(self, classification: ClassificationResult) -> List[SourcedContent]:
        """Get targeted content from Hugging Face corpus"""
        sources = []

        try:
            # Check if datasets package is available
            if not HAS_DATASETS:
                self.logger.warning("Datasets package not available - using fallback content")
                return self._get_fallback_content(classification)

            # Load dataset with streaming
            dataset = load_dataset(
                "isaacus/open-australian-legal-corpus",
                split="corpus",
                streaming=True
            )

            # Get revenue-specific search terms
            search_terms = classification.search_terms
            count = 0

            for doc in dataset:
                if count >= 30:  # Limit search
                    break

                title = doc.get('title', '').lower()
                content = doc.get('content', '').lower()
                jurisdiction = doc.get('jurisdiction', '').lower()

                # Check if document is NSW-related and relevant to classification
                is_nsw = any(term in title or term in jurisdiction for term in ['nsw', 'new south wales'])
                is_relevant = any(term.lower() in title or term.lower() in content[:2000]
                                for term in search_terms)

                if is_nsw and is_relevant:
                    # Extract most relevant sections
                    relevant_content = self._extract_corpus_relevant_sections(
                        doc.get('content', ''), classification
                    )

                    if relevant_content:
                        source = SourcedContent(
                            id=f"corpus_{hash(doc.get('title', ''))}",
                            title=doc.get('title', 'Unknown Document'),
                            content=relevant_content,
                            source_type='huggingface',
                            relevance_score=self._calculate_corpus_relevance(
                                relevant_content, classification
                            )
                        )
                        sources.append(source)

                count += 1

        except Exception as e:
            logger.error(f"Corpus retrieval failed: {e}")

        return sources

    def _get_fallback_content(self, classification: ClassificationResult) -> List[SourcedContent]:
        """Fallback content when datasets package is not available"""
        fallback_sources = []

        # Basic NSW Revenue content for common questions
        if classification.revenue_type.value in ['payroll_tax', 'land_tax', 'stamp_duty']:
            fallback_content = {
                'payroll_tax': "NSW Payroll Tax is levied on wages paid by employers. The current rate is 5.45% for employers with payroll above the threshold of $1.2 million. Small businesses may be exempt from payroll tax if their total payroll is below this threshold.",
                'land_tax': "NSW Land Tax is an annual tax on land ownership. The tax-free threshold is $755,000 for 2024. Premium rates apply to land valued over $4 million. Primary residences are generally exempt from land tax.",
                'stamp_duty': "NSW Stamp Duty is payable on property transfers, motor vehicle registrations, and certain business transactions. First home buyers may be eligible for concessions or exemptions on properties under certain value thresholds."
            }

            content = fallback_content.get(classification.revenue_type.value, "General NSW Revenue information")
            fallback_sources.append(SourcedContent(
                content=content,
                source="NSW Revenue - General Information",
                confidence=0.7,
                section="General Guidelines"
            ))

        return fallback_sources

    def _extract_relevant_sections(self, content: str, search_terms: List[str],
                                 intent: QuestionIntent) -> str:
        """Extract sections most relevant to the search terms and intent"""
        paragraphs = content.split('\n\n')
        relevant_paragraphs = []

        for paragraph in paragraphs:
            if len(paragraph.strip()) < 50:  # Skip very short paragraphs
                continue

            # Score paragraph based on search terms
            score = 0
            paragraph_lower = paragraph.lower()

            for term in search_terms:
                if term.lower() in paragraph_lower:
                    score += 1

            # Boost for intent-specific content
            if intent == QuestionIntent.CALCULATION and any(
                word in paragraph_lower for word in ['rate', 'calculate', 'amount', '%', '$']
            ):
                score += 2
            elif intent == QuestionIntent.PENALTY and any(
                word in paragraph_lower for word in ['penalty', 'fine', 'interest', 'late']
            ):
                score += 2

            if score > 0:
                relevant_paragraphs.append((score, paragraph))

        # Sort by score and return top paragraphs
        relevant_paragraphs.sort(key=lambda x: x[0], reverse=True)
        return '\n\n'.join([p[1] for p in relevant_paragraphs[:5]])  # Top 5 paragraphs

    def _is_content_relevant(self, content: str, classification: ClassificationResult) -> bool:
        """Check if content is relevant to the classification"""
        content_lower = content.lower()

        # Check for search terms
        term_matches = sum(1 for term in classification.search_terms
                          if term.lower() in content_lower)

        return term_matches >= 2  # At least 2 search terms must match

    def _extract_relevant_text(self, content: str, classification: ClassificationResult) -> str:
        """Extract most relevant text from website content"""
        # Split into sentences and score
        sentences = content.split('. ')
        scored_sentences = []

        for sentence in sentences:
            if len(sentence.strip()) < 30:
                continue

            score = 0
            sentence_lower = sentence.lower()

            # Score based on search terms
            for term in classification.search_terms:
                if term.lower() in sentence_lower:
                    score += 1

            if score > 0:
                scored_sentences.append((score, sentence))

        # Return top sentences
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        return '. '.join([s[1] for s in scored_sentences[:10]])  # Top 10 sentences

    def _extract_corpus_relevant_sections(self, content: str,
                                        classification: ClassificationResult) -> str:
        """Extract relevant sections from corpus content"""
        # Similar to _extract_relevant_sections but optimized for corpus content
        return self._extract_relevant_sections(
            content, classification.search_terms, classification.question_intent
        )[:1500]  # Limit corpus content length

    def _rank_sources_by_classification(self, question: str, classification: ClassificationResult,
                                      sources: List[SourcedContent]) -> List[SourcedContent]:
        """Rank sources based on their relevance to the specific classification"""

        for source in sources:
            # Base score is the existing relevance score
            score = source.relevance_score

            # Boost legislation sources for definition/compliance questions
            if (source.source_type == 'legislation' and
                classification.question_intent in [QuestionIntent.DEFINITION, QuestionIntent.COMPLIANCE]):
                score += 0.3

            # Boost website sources for process/deadline questions
            if (source.source_type == 'website' and
                classification.question_intent in [QuestionIntent.PROCESS, QuestionIntent.DEADLINE]):
                score += 0.2

            # Boost sources that contain entities from the question
            for entity in classification.key_entities:
                if entity.lower() in source.content.lower():
                    score += 0.1

            source.relevance_score = min(score, 1.0)

        # Sort by relevance score
        return sorted(sources, key=lambda s: s.relevance_score, reverse=True)

    def _highlight_relevant_passages(self, question: str,
                                   sources: List[SourcedContent]) -> List[SourcedContent]:
        """Identify and highlight specific text passages that answer the question"""

        for source in sources:
            highlighted_passages = []

            # Split content into sentences
            sentences = source.content.split('. ')

            for sentence in sentences:
                if len(sentence.strip()) < 20:
                    continue

                # Use simple relevance scoring for now
                # In a more sophisticated system, this would use semantic similarity
                if self._is_sentence_answering(sentence, question):
                    highlighted_passages.append(sentence.strip())

                if len(highlighted_passages) >= 3:  # Limit to top 3 passages
                    break

            source.highlighted_text = highlighted_passages

        return sources

    def _is_sentence_answering(self, sentence: str, question: str) -> bool:
        """Simple check if a sentence likely answers the question"""
        question_words = set(question.lower().split())
        sentence_words = set(sentence.lower().split())

        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were'}
        question_words -= common_words
        sentence_words -= common_words

        # Check overlap
        overlap = len(question_words.intersection(sentence_words))
        return overlap >= 2  # At least 2 meaningful words in common

    def _calculate_legislation_relevance(self, content: str,
                                       classification: ClassificationResult) -> float:
        """Calculate relevance score for legislation content"""
        score = 0.5  # Base score for legislation

        content_lower = content.lower()

        # Boost for search term matches
        for term in classification.search_terms:
            if term.lower() in content_lower:
                score += 0.1

        # Intent-specific boosts
        if classification.question_intent == QuestionIntent.DEFINITION:
            if any(word in content_lower for word in ['means', 'definition', 'defined as']):
                score += 0.2

        return min(score, 1.0)

    def _calculate_website_relevance(self, content: str,
                                   classification: ClassificationResult) -> float:
        """Calculate relevance score for website content"""
        score = 0.3  # Base score for website

        content_lower = content.lower()

        # Boost for search term matches
        for term in classification.search_terms:
            if term.lower() in content_lower:
                score += 0.1

        # Boost for practical information
        if any(word in content_lower for word in ['how to', 'apply', 'calculate', 'rate']):
            score += 0.2

        return min(score, 1.0)

    def _calculate_corpus_relevance(self, content: str,
                                  classification: ClassificationResult) -> float:
        """Calculate relevance score for corpus content"""
        score = 0.4  # Base score for corpus

        content_lower = content.lower()

        # Boost for search term matches
        for term in classification.search_terms:
            if term.lower() in content_lower:
                score += 0.1

        return min(score, 1.0)

    def _extract_page_title(self, soup) -> str:
        """Extract page title from BeautifulSoup object"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()

        return "NSW Revenue Page"


def main():
    """Test the targeted sourcing agent"""
    from .classification_agent import ClassificationAgent

    # Initialize agents
    classifier = ClassificationAgent()
    sourcing_agent = TargetedSourcingAgent()

    test_question = "What is the payroll tax rate for a business with $2 million in wages?"

    # Classify the question
    classification = classifier.classify_question(test_question)
    print(f"Classification: {classification.revenue_type.value}, {classification.question_intent.value}")

    # Get targeted sources
    sources = sourcing_agent.get_targeted_sources(test_question, classification, max_sources=5)

    print(f"\nFound {len(sources)} targeted sources:")
    for i, source in enumerate(sources, 1):
        print(f"\n{i}. {source.title} ({source.source_type})")
        print(f"   Relevance: {source.relevance_score:.2f}")
        print(f"   Content preview: {source.content[:150]}...")
        if source.highlighted_text:
            print(f"   Key passages: {len(source.highlighted_text)}")


if __name__ == "__main__":
    main()