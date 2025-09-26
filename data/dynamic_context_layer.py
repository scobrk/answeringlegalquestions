"""
Dynamic Context Layer for NSW Revenue AI Assistant
Real-time content retrieval and indexing based on user queries
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup

from openai import OpenAI
from datasets import load_dataset
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContextDocument:
    """Represents a document in the context layer"""
    id: str
    title: str
    content: str
    source: str  # 'nsw_revenue_web', 'huggingface', 'local'
    url: Optional[str] = None
    relevance_score: float = 0.0
    section: Optional[str] = None
    act_name: Optional[str] = None


class DynamicContextLayer:
    """
    Dynamic context retrieval system that indexes and queries content in real-time
    """

    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Content sources
        self.nsw_revenue_base_url = "https://www.revenue.nsw.gov.au"
        self.legislation_index_url = "https://www.revenue.nsw.gov.au/about/legislation-and-rulings/legislation"

        # Cached indexes
        self.nsw_content_index = {}
        self.hf_content_index = {}
        self.combined_index = {}

        # Request headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

    def get_relevant_context(self, query: str, max_docs: int = 5) -> List[ContextDocument]:
        """
        Main method: Get relevant context documents for a query

        Args:
            query: User query
            max_docs: Maximum number of documents to return

        Returns:
            List of relevant ContextDocument objects
        """
        logger.info(f"Getting relevant context for query: {query}")

        # Step 1: Identify query intent and extract keywords
        query_keywords = self._extract_query_keywords(query)

        # Step 2: Query multiple sources in parallel
        context_docs = []

        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit tasks for parallel execution
            nsw_future = executor.submit(self._query_nsw_revenue_web, query, query_keywords)
            hf_future = executor.submit(self._query_huggingface_corpus, query, query_keywords)
            local_future = executor.submit(self._query_local_content, query, query_keywords)

            # Collect results
            try:
                nsw_docs = nsw_future.result(timeout=30)
                context_docs.extend(nsw_docs)
            except Exception as e:
                logger.warning(f"NSW Revenue web query failed: {e}")

            try:
                hf_docs = hf_future.result(timeout=45)
                context_docs.extend(hf_docs)
            except Exception as e:
                logger.warning(f"Hugging Face query failed: {e}")

            try:
                local_docs = local_future.result(timeout=10)
                context_docs.extend(local_docs)
            except Exception as e:
                logger.warning(f"Local content query failed: {e}")

        # Step 3: Rank and filter results
        ranked_docs = self._rank_documents_by_relevance(query, context_docs)

        # Step 4: Return top results
        return ranked_docs[:max_docs]

    def _extract_query_keywords(self, query: str) -> List[str]:
        """Extract key terms and concepts from the query"""
        # NSW Revenue specific terms
        revenue_terms = [
            'payroll tax', 'land tax', 'stamp duty', 'duties', 'conveyance duty',
            'mortgage duty', 'first home buyer', 'exemption', 'threshold',
            'rate', 'calculation', 'assessment', 'penalty', 'fine',
            'revenue administration', 'objection', 'appeal', 'enforcement'
        ]

        query_lower = query.lower()
        keywords = []

        # Add matched revenue terms
        for term in revenue_terms:
            if term in query_lower:
                keywords.append(term)

        # Add numeric values (amounts, percentages, years)
        import re
        numbers = re.findall(r'\$?[\d,]+\.?\d*%?', query)
        keywords.extend(numbers)

        # Add basic keywords from query
        words = query_lower.split()
        important_words = [w for w in words if len(w) > 3 and w not in ['what', 'how', 'when', 'where', 'the', 'and', 'for', 'with']]
        keywords.extend(important_words[:5])  # Limit to top 5 words

        return list(set(keywords))

    def _query_nsw_revenue_web(self, query: str, keywords: List[str]) -> List[ContextDocument]:
        """Query NSW Revenue website dynamically"""
        logger.info("Querying NSW Revenue website...")

        docs = []

        try:
            # Get legislation index
            response = requests.get(self.legislation_index_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find relevant legislation links
            links = soup.find_all('a', href=True)
            relevant_links = []

            for link in links:
                link_text = link.get_text().lower()
                href = link['href']

                # Check if link is relevant to keywords
                if any(keyword.lower() in link_text for keyword in keywords):
                    if href.startswith('/') and 'legislation' in href:
                        full_url = self.nsw_revenue_base_url + href
                        relevant_links.append((link_text, full_url))

            # Fetch content from top 3 relevant links
            for title, url in relevant_links[:3]:
                try:
                    doc_response = requests.get(url, headers=self.headers, timeout=10)
                    doc_soup = BeautifulSoup(doc_response.content, 'html.parser')

                    # Extract main content
                    content_div = doc_soup.find('div', class_=['content', 'main-content', 'article'])
                    if content_div:
                        content = content_div.get_text(strip=True)[:2000]  # Limit content

                        doc = ContextDocument(
                            id=f"nsw_web_{hash(url)}",
                            title=title.title(),
                            content=content,
                            source='nsw_revenue_web',
                            url=url,
                            relevance_score=self._calculate_relevance(query, content)
                        )
                        docs.append(doc)

                except Exception as e:
                    logger.warning(f"Failed to fetch {url}: {e}")
                    continue

        except Exception as e:
            logger.error(f"NSW Revenue web query failed: {e}")

        logger.info(f"Retrieved {len(docs)} documents from NSW Revenue website")
        return docs

    def _query_huggingface_corpus(self, query: str, keywords: List[str]) -> List[ContextDocument]:
        """Query Hugging Face Australian Legal Corpus"""
        logger.info("Querying Hugging Face corpus...")

        docs = []

        try:
            # Load dataset (with caching)
            dataset = load_dataset(
                "isaacus/open-australian-legal-corpus",
                split="corpus",  # Use 'corpus' split instead of 'train'
                streaming=True  # Use streaming to avoid loading entire dataset
            )

            # Filter for NSW Revenue related documents
            count = 0
            for doc in dataset:
                if count >= 50:  # Limit search to prevent timeout
                    break

                title = doc.get('title', '').lower()
                content = doc.get('content', '').lower()
                jurisdiction = doc.get('jurisdiction', '').lower()

                # Check relevance to NSW Revenue
                is_nsw = any(term in title or term in jurisdiction for term in ['nsw', 'new south wales'])
                is_revenue_related = any(keyword.lower() in title or keyword.lower() in content[:1000]
                                       for keyword in keywords)

                if is_nsw and is_revenue_related:
                    context_doc = ContextDocument(
                        id=f"hf_{hash(doc.get('title', ''))}",
                        title=doc.get('title', 'Unknown Title'),
                        content=doc.get('content', '')[:2000],  # Limit content
                        source='huggingface',
                        relevance_score=self._calculate_relevance(query, doc.get('content', ''))
                    )
                    docs.append(context_doc)

                count += 1

        except Exception as e:
            logger.error(f"Hugging Face query failed: {e}")

        logger.info(f"Retrieved {len(docs)} documents from Hugging Face corpus")
        return docs

    def _query_local_content(self, query: str, keywords: List[str]) -> List[ContextDocument]:
        """Query comprehensive local legislation files from legislation_v2"""
        logger.info("Querying comprehensive local content...")

        docs = []

        try:
            # Use the comprehensive legislation_v2 structure
            legislation_dir = Path("./data/legislation_v2")
            old_legislation_dir = Path("./data/legislation")

            # Process new comprehensive structure first
            if legislation_dir.exists():
                for md_file in legislation_dir.glob("**/*.md"):
                    try:
                        with open(md_file, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Check relevance
                        if any(keyword.lower() in content.lower() for keyword in keywords) or \
                           any(keyword.lower() in md_file.name.lower() for keyword in keywords):

                            relative_path = md_file.relative_to(legislation_dir)
                            category = str(relative_path.parent).replace('/', '_').replace('\\', '_')

                            doc = ContextDocument(
                                id=f"comprehensive_{md_file.stem}_{category}",
                                title=md_file.stem.replace('_', ' ').title(),
                                content=content[:3000],  # Increased limit for comprehensive content
                                source='local_comprehensive',
                                act_name=md_file.stem,
                                section=category,
                                relevance_score=self._calculate_relevance(query, content)
                            )
                            docs.append(doc)

                    except Exception as e:
                        logger.warning(f"Could not process {md_file}: {e}")
                        continue

            # Fallback to old structure if needed
            if old_legislation_dir.exists() and len(docs) < 3:
                for txt_file in old_legislation_dir.glob("*.txt"):
                    with open(txt_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check relevance
                    if any(keyword.lower() in content.lower() for keyword in keywords):
                        doc = ContextDocument(
                            id=f"legacy_{txt_file.stem}",
                            title=txt_file.stem.replace('_', ' ').title(),
                            content=content[:2000],  # Limit content
                            source='local_legacy',
                            act_name=txt_file.stem,
                            relevance_score=self._calculate_relevance(query, content)
                        )
                        docs.append(doc)

        except Exception as e:
            logger.error(f"Local content query failed: {e}")

        logger.info(f"Retrieved {len(docs)} documents from local content")
        return docs

    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score between query and content"""
        try:
            # Simple relevance scoring
            query_words = set(query.lower().split())
            content_words = set(content.lower().split())

            # Jaccard similarity
            intersection = len(query_words.intersection(content_words))
            union = len(query_words.union(content_words))

            if union == 0:
                return 0.0

            base_score = intersection / union

            # Boost for exact phrase matches
            if query.lower() in content.lower():
                base_score += 0.3

            # Boost for NSW Revenue specific terms
            revenue_terms = ['payroll tax', 'land tax', 'stamp duty', 'duties']
            for term in revenue_terms:
                if term in query.lower() and term in content.lower():
                    base_score += 0.2

            return min(base_score, 1.0)

        except Exception:
            return 0.0

    def _rank_documents_by_relevance(self, query: str, docs: List[ContextDocument]) -> List[ContextDocument]:
        """Rank documents by relevance to the query"""

        # Sort by relevance score (descending)
        ranked_docs = sorted(docs, key=lambda d: d.relevance_score, reverse=True)

        # Boost scores for source diversity
        source_counts = {}
        for i, doc in enumerate(ranked_docs):
            source_counts[doc.source] = source_counts.get(doc.source, 0) + 1

            # Boost first occurrence of each source
            if source_counts[doc.source] == 1:
                doc.relevance_score += 0.1

        # Re-sort after adjustment
        ranked_docs = sorted(ranked_docs, key=lambda d: d.relevance_score, reverse=True)

        return ranked_docs

    def format_context_for_llm(self, context_docs: List[ContextDocument]) -> str:
        """Format context documents for LLM consumption"""

        if not context_docs:
            return "No relevant context documents found."

        formatted_context = "=== RELEVANT NSW REVENUE LEGISLATION CONTEXT ===\n\n"

        for i, doc in enumerate(context_docs, 1):
            formatted_context += f"Document {i}: {doc.title}\n"
            formatted_context += f"Source: {doc.source}\n"
            formatted_context += f"Relevance: {doc.relevance_score:.3f}\n"
            if doc.url:
                formatted_context += f"URL: {doc.url}\n"
            formatted_context += f"Content: {doc.content}\n"
            formatted_context += "---\n\n"

        return formatted_context

    def get_context_summary(self, context_docs: List[ContextDocument]) -> Dict:
        """Get summary information about retrieved context"""

        if not context_docs:
            return {"total_docs": 0, "sources": {}, "avg_relevance": 0.0}

        sources = {}
        total_relevance = 0

        for doc in context_docs:
            sources[doc.source] = sources.get(doc.source, 0) + 1
            total_relevance += doc.relevance_score

        return {
            "total_docs": len(context_docs),
            "sources": sources,
            "avg_relevance": total_relevance / len(context_docs),
            "top_relevance": max(doc.relevance_score for doc in context_docs)
        }


def main():
    """Test the dynamic context layer"""
    context_layer = DynamicContextLayer()

    test_queries = [
        "What is the payroll tax rate in NSW?",
        "How do I calculate land tax for a $2 million property?",
        "What are the first home buyer stamp duty concessions?"
    ]

    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print('='*50)

        start_time = time.time()
        context_docs = context_layer.get_relevant_context(query, max_docs=3)
        end_time = time.time()

        summary = context_layer.get_context_summary(context_docs)

        print(f"Retrieved {summary['total_docs']} documents in {end_time-start_time:.2f}s")
        print(f"Sources: {summary['sources']}")
        print(f"Average relevance: {summary['avg_relevance']:.3f}")

        for i, doc in enumerate(context_docs, 1):
            print(f"\n{i}. {doc.title} ({doc.source})")
            print(f"   Relevance: {doc.relevance_score:.3f}")
            print(f"   Content: {doc.content[:150]}...")


if __name__ == "__main__":
    main()