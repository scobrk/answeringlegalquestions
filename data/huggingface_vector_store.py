"""
Hugging Face Vector Store for Australian Legal Corpus
Dynamic integration with NSW Revenue legislation from HF dataset
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import logging
from openai import OpenAI
import faiss
from datasets import load_dataset
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HuggingFaceVectorStore:
    """
    Vector store that dynamically loads and searches the Australian Legal Corpus
    from Hugging Face for NSW Revenue related documents
    """

    def __init__(self, cache_dir: str = "./data/hf_cache", index_dir: str = "./data/hf_vector_index"):
        self.cache_dir = Path(cache_dir)
        self.index_dir = Path(index_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_dir.mkdir(parents=True, exist_ok=True)

        # OpenAI client for embeddings
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Dataset and index
        self.dataset = None
        self.nsw_revenue_docs = []
        self.index = None
        self.embeddings = []

        # Index files
        self.index_file = self.index_dir / "hf_faiss_index.bin"
        self.docs_file = self.index_dir / "hf_documents.pkl"
        self.metadata_file = self.index_dir / "hf_metadata.json"

        # NSW Revenue related keywords for filtering
        self.nsw_revenue_keywords = [
            'duties act', 'payroll tax', 'land tax', 'stamp duty',
            'nsw revenue', 'new south wales revenue', 'taxation',
            'revenue administration', 'fines act', 'first home owner',
            'conveyance duty', 'mortgage duty', 'transfer duty',
            'principal place of residence', 'tax exemption',
            'tax threshold', 'penalty notice', 'enforcement',
            'assessment', 'objection', 'appeal'
        ]

        # Load or create index
        self._initialize()

    def _initialize(self):
        """Initialize the vector store"""
        try:
            if self._index_exists():
                logger.info("Loading existing Hugging Face vector index...")
                self._load_index()
            else:
                logger.info("Creating new Hugging Face vector index...")
                self._create_index()
        except Exception as e:
            logger.error(f"Error initializing Hugging Face vector store: {e}")
            # Create minimal fallback index
            self._create_fallback_index()

    def _load_dataset(self):
        """Load the Australian Legal Corpus from Hugging Face"""
        try:
            logger.info("Loading Australian Legal Corpus from Hugging Face...")

            # Get HuggingFace token
            hf_token = os.getenv('HUGGINGFACE_TOKEN')
            if not hf_token:
                logger.error("HUGGINGFACE_TOKEN not found in environment variables")
                return False

            # Load dataset with authentication and caching
            self.dataset = load_dataset(
                "isaacus/open-australian-legal-corpus",
                split="train",
                cache_dir=str(self.cache_dir),
                token=hf_token
            )

            logger.info(f"Loaded {len(self.dataset)} documents from Australian Legal Corpus")
            return True

        except Exception as e:
            logger.error(f"Failed to load Hugging Face dataset: {e}")
            logger.error("Check if HUGGINGFACE_TOKEN is correct and you have access to the dataset")
            return False

    def _filter_nsw_revenue_docs(self):
        """Filter dataset for NSW Revenue related documents"""
        if not self.dataset:
            return []

        logger.info("Filtering documents for NSW Revenue legislation...")
        nsw_revenue_docs = []

        for doc in self.dataset:
            title = doc.get('title', '').lower()
            content = doc.get('content', '').lower()
            jurisdiction = doc.get('jurisdiction', '').lower()

            # Check if document is NSW related and revenue related
            is_nsw = any(term in title or term in jurisdiction for term in ['nsw', 'new south wales'])
            is_revenue = any(keyword in title or keyword in content[:2000] for keyword in self.nsw_revenue_keywords)

            if is_nsw and is_revenue:
                # Clean and structure the document
                clean_doc = {
                    'title': doc.get('title', 'Unknown Title'),
                    'content': doc.get('content', ''),
                    'jurisdiction': doc.get('jurisdiction', 'Unknown'),
                    'document_type': doc.get('type', 'legislation'),
                    'source': 'huggingface_australian_legal_corpus',
                    'relevance_score': self._calculate_relevance_score(title, content)
                }
                nsw_revenue_docs.append(clean_doc)

            # Limit to prevent memory issues
            if len(nsw_revenue_docs) >= 500:
                break

        logger.info(f"Filtered {len(nsw_revenue_docs)} NSW Revenue documents")
        return nsw_revenue_docs

    def _calculate_relevance_score(self, title: str, content: str) -> float:
        """Calculate relevance score for NSW Revenue content"""
        score = 0.0

        # Title relevance (higher weight)
        for keyword in self.nsw_revenue_keywords:
            if keyword in title.lower():
                score += 0.3

        # Content relevance (lower weight)
        content_sample = content[:1000].lower()
        for keyword in self.nsw_revenue_keywords:
            if keyword in content_sample:
                score += 0.1

        return min(score, 1.0)

    def _create_index(self):
        """Create new vector index from Hugging Face data"""
        # Load dataset
        if not self._load_dataset():
            logger.warning("Failed to load dataset, creating fallback index")
            self._create_fallback_index()
            return

        # Filter for NSW Revenue documents
        self.nsw_revenue_docs = self._filter_nsw_revenue_docs()

        if not self.nsw_revenue_docs:
            logger.warning("No NSW Revenue documents found, creating fallback index")
            self._create_fallback_index()
            return

        # Generate embeddings
        self._generate_embeddings()

        # Create FAISS index
        self._create_faiss_index()

        # Save to disk
        self._save_index()

    def _generate_embeddings(self):
        """Generate embeddings for filtered documents"""
        logger.info(f"Generating embeddings for {len(self.nsw_revenue_docs)} documents...")

        embeddings = []
        batch_size = 10  # Smaller batches for HF data

        for i in range(0, len(self.nsw_revenue_docs), batch_size):
            batch = self.nsw_revenue_docs[i:i + batch_size]

            # Prepare text for embedding (title + content preview)
            batch_texts = []
            for doc in batch:
                text = f"{doc['title']}\n\n{doc['content'][:1500]}"  # Limit content length
                batch_texts.append(text)

            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=batch_texts
                )

                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

                logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(self.nsw_revenue_docs) + batch_size - 1)//batch_size}")

                # Rate limiting
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error generating embeddings for batch {i//batch_size + 1}: {e}")
                # Create zero embeddings as fallback
                fallback_embeddings = [[0.0] * 1536 for _ in batch]
                embeddings.extend(fallback_embeddings)

        self.embeddings = embeddings

    def _create_faiss_index(self):
        """Create FAISS index from embeddings"""
        if not self.embeddings:
            raise ValueError("No embeddings to index")

        # Convert to numpy array
        embeddings_array = np.array(self.embeddings).astype('float32')

        # Create FAISS index
        dimension = embeddings_array.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings_array)

        # Add embeddings to index
        self.index.add(embeddings_array)

        logger.info(f"Created FAISS index with {self.index.ntotal} vectors")

    def _save_index(self):
        """Save index and documents to disk"""
        # Save FAISS index
        faiss.write_index(self.index, str(self.index_file))

        # Save documents
        with open(self.docs_file, 'wb') as f:
            pickle.dump(self.nsw_revenue_docs, f)

        # Save metadata
        metadata = {
            'total_documents': len(self.nsw_revenue_docs),
            'embedding_model': 'text-embedding-3-small',
            'dimension': 1536,
            'source': 'huggingface_australian_legal_corpus',
            'created_at': time.time(),
            'nsw_revenue_keywords': self.nsw_revenue_keywords
        }

        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"✅ Saved Hugging Face index to {self.index_dir}")

    def _load_index(self):
        """Load index and documents from disk"""
        # Load FAISS index
        self.index = faiss.read_index(str(self.index_file))

        # Load documents
        with open(self.docs_file, 'rb') as f:
            self.nsw_revenue_docs = pickle.load(f)

        logger.info(f"✅ Loaded Hugging Face index with {len(self.nsw_revenue_docs)} documents")

    def _index_exists(self):
        """Check if index files exist"""
        return (self.index_file.exists() and
                self.docs_file.exists() and
                self.metadata_file.exists())

    def _create_fallback_index(self):
        """Create fallback index when HF loading fails"""
        logger.info("Creating fallback index with minimal NSW Revenue content...")

        # Minimal fallback documents
        self.nsw_revenue_docs = [
            {
                'title': 'Payroll Tax Act 2007 (NSW)',
                'content': 'The rate of payroll tax is 5.45%. The tax-free threshold is $1,200,000.',
                'jurisdiction': 'NSW',
                'document_type': 'legislation',
                'source': 'fallback',
                'relevance_score': 1.0
            },
            {
                'title': 'Duties Act 1997 (NSW)',
                'content': 'Stamp duty rates apply to property transfers. First home buyer concessions available.',
                'jurisdiction': 'NSW',
                'document_type': 'legislation',
                'source': 'fallback',
                'relevance_score': 1.0
            },
            {
                'title': 'Land Tax Act 1956 (NSW)',
                'content': 'Land tax applies to land above the tax-free threshold of $969,000.',
                'jurisdiction': 'NSW',
                'document_type': 'legislation',
                'source': 'fallback',
                'relevance_score': 1.0
            }
        ]

        # Create simple embeddings
        try:
            texts = [f"{doc['title']}\n{doc['content']}" for doc in self.nsw_revenue_docs]
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            self.embeddings = [item.embedding for item in response.data]
        except Exception:
            # Create zero embeddings if OpenAI fails
            self.embeddings = [[0.0] * 1536 for _ in self.nsw_revenue_docs]

        # Create minimal FAISS index
        if self.embeddings:
            self._create_faiss_index()

    def search_nsw_revenue_docs(self, query: str, k: int = 10, threshold: float = 0.5) -> List[Dict]:
        """Search for NSW Revenue documents relevant to query"""
        if not self.index or not self.nsw_revenue_docs:
            logger.warning("No index available for search")
            return []

        try:
            # Generate query embedding
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=[query]
            )
            query_embedding = np.array([response.data[0].embedding]).astype('float32')

            # Normalize query embedding
            faiss.normalize_L2(query_embedding)

            # Search
            scores, indices = self.index.search(query_embedding, k)

            # Filter and format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= threshold and idx < len(self.nsw_revenue_docs):
                    doc = self.nsw_revenue_docs[idx].copy()
                    doc['similarity_score'] = float(score)
                    results.append(doc)

            logger.info(f"Found {len(results)} relevant NSW Revenue documents for query: {query[:50]}...")
            return results

        except Exception as e:
            logger.error(f"Error searching Hugging Face documents: {e}")
            return []

    def get_corpus_info(self) -> Dict:
        """Get information about the loaded corpus"""
        return {
            'total_documents': len(self.nsw_revenue_docs),
            'source': 'Hugging Face Australian Legal Corpus',
            'focus': 'NSW Revenue Legislation',
            'embedding_model': 'text-embedding-3-small',
            'last_updated': time.time(),
            'available': bool(self.index and self.nsw_revenue_docs)
        }

    def refresh_index(self):
        """Refresh the index by reloading from Hugging Face"""
        logger.info("Refreshing Hugging Face index...")

        # Clear existing data
        self.dataset = None
        self.nsw_revenue_docs = []
        self.index = None
        self.embeddings = []

        # Recreate index
        self._create_index()


def main():
    """Test the Hugging Face Vector Store"""
    store = HuggingFaceVectorStore()

    # Test search
    test_queries = [
        "What is the payroll tax rate in NSW?",
        "Land tax exemptions for principal residence",
        "First home buyer stamp duty concessions"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        results = store.search_nsw_revenue_docs(query, k=3)

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   Score: {result['similarity_score']:.3f}")
            print(f"   Source: {result['source']}")
            print(f"   Content: {result['content'][:100]}...")

    # Show corpus info
    info = store.get_corpus_info()
    print(f"\n📊 Corpus Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()