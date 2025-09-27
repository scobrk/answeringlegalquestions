"""
Hybrid Search Implementation for NSW Revenue Legislation
Combines BM25 keyword search with Legal-BERT semantic search for high relevance
"""

import os
import json
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import logging
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HybridSearchEngine:
    """
    Hybrid search engine combining BM25 keyword search with Legal-BERT semantic search
    Optimized for NSW Revenue legislation retrieval
    """

    def __init__(self, data_dir: str = "./data/legislation_v2", cache_dir: str = "./data/hybrid_cache"):
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.documents = []
        self.document_metadata = []
        self.bm25_index = None
        self.embeddings = None
        self.legal_model = None

        # Cache files
        self.documents_cache = self.cache_dir / "documents.pkl"
        self.bm25_cache = self.cache_dir / "bm25_index.pkl"
        self.embeddings_cache = self.cache_dir / "embeddings.npy"
        self.metadata_cache = self.cache_dir / "metadata.json"

        # Download NLTK data if needed
        try:
            nltk.data.find('tokenizers/punkt_tab')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            logger.info("Downloading NLTK data...")
            nltk.download('punkt_tab', quiet=True)
            nltk.download('stopwords', quiet=True)

        self.stop_words = set(stopwords.words('english'))
        # Add legal-specific stop words
        legal_stop_words = {'act', 'section', 'subsection', 'paragraph', 'clause', 'part', 'division'}
        self.stop_words.update(legal_stop_words)

    def initialize(self, force_rebuild: bool = False) -> None:
        """Initialize the hybrid search engine"""
        logger.info("Initializing hybrid search engine...")

        # Load or create document index
        if not force_rebuild and self._cache_exists():
            logger.info("Loading from cache...")
            self._load_from_cache()
        else:
            logger.info("Building new index...")
            self._build_index()
            self._save_to_cache()

        logger.info(f"Hybrid search engine ready with {len(self.documents)} documents")

    def _cache_exists(self) -> bool:
        """Check if all cache files exist"""
        return (self.documents_cache.exists() and
                self.bm25_cache.exists() and
                self.embeddings_cache.exists() and
                self.metadata_cache.exists())

    def _build_index(self) -> None:
        """Build the hybrid search index from scratch"""
        logger.info("Loading legislation documents...")
        self._load_documents()

        logger.info("Loading Legal-BERT model...")
        self._load_legal_model()

        logger.info("Creating BM25 index...")
        self._create_bm25_index()

        logger.info("Generating Legal-BERT embeddings...")
        self._create_embeddings()

    def _load_documents(self) -> None:
        """Load all legislation documents from the data directory"""
        self.documents = []
        self.document_metadata = []

        # Process all markdown files recursively
        for md_file in self.data_dir.glob("**/*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract category from path
                relative_path = md_file.relative_to(self.data_dir)
                category_parts = relative_path.parts[:-1]  # Remove filename
                category = "_".join(category_parts) if category_parts else "general"

                # Extract revenue type from category
                revenue_type = self._extract_revenue_type(category, md_file.stem)

                # Create document sections for better retrieval
                sections = self._split_document_into_sections(content, md_file.stem)

                for i, section in enumerate(sections):
                    self.documents.append(section['content'])
                    self.document_metadata.append({
                        'file_path': str(md_file),
                        'act_name': md_file.stem,
                        'section_title': section['title'],
                        'section_number': section.get('section_number', f"part_{i}"),
                        'category': category,
                        'revenue_type': revenue_type,
                        'file_size': len(content),
                        'section_index': i
                    })

                logger.info(f"Processed: {relative_path} -> {len(sections)} sections")

            except Exception as e:
                logger.warning(f"Could not process {md_file}: {e}")
                continue

        logger.info(f"Loaded {len(self.documents)} document sections from {len(list(self.data_dir.glob('**/*.md')))} files")

    def _extract_revenue_type(self, category: str, filename: str) -> str:
        """Extract revenue type from category path and filename"""
        # Map categories to revenue types
        type_mapping = {
            'property_related': 'property_tax',
            'business_taxation': 'business_tax',
            'motor_vehicle': 'motor_vehicle_tax',
            'gaming_and_liquor': 'gaming_liquor_tax',
            'royalties': 'royalties',
            'environmental': 'environmental_levy',
            'insurance_and_levies': 'insurance_levy',
            'fines_and_penalties': 'fines_penalties',
            'administration': 'administration',
            'grants_and_schemes': 'grants'
        }

        for key, value in type_mapping.items():
            if key in category.lower():
                return value

        # Fallback to filename analysis
        if 'land_tax' in filename.lower():
            return 'property_tax'
        elif 'payroll' in filename.lower():
            return 'business_tax'
        elif 'motor' in filename.lower() or 'vehicle' in filename.lower():
            return 'motor_vehicle_tax'

        return 'general'

    def _split_document_into_sections(self, content: str, act_name: str) -> List[Dict]:
        """Split document into logical sections for better retrieval"""
        sections = []

        # Split by major headings
        lines = content.split('\n')
        current_section = []
        current_title = act_name
        current_section_number = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section headers
            if (line.startswith('# ') or
                line.startswith('## ') or
                line.startswith('### ') or
                re.match(r'^Section \d+', line, re.IGNORECASE)):

                # Save previous section
                if current_section:
                    sections.append({
                        'title': current_title,
                        'content': '\n'.join(current_section),
                        'section_number': current_section_number
                    })

                # Start new section
                current_title = line.lstrip('#').strip()
                current_section = [line]

                # Extract section number if present
                section_match = re.search(r'Section (\d+[A-Z]*)', line, re.IGNORECASE)
                current_section_number = section_match.group(1) if section_match else None
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            sections.append({
                'title': current_title,
                'content': '\n'.join(current_section),
                'section_number': current_section_number
            })

        # If no sections were created, treat entire document as one section
        if not sections:
            sections.append({
                'title': act_name,
                'content': content,
                'section_number': None
            })

        return sections

    def _load_legal_model(self) -> None:
        """Load the Legal-BERT model for semantic embeddings"""
        try:
            # Try legal-specific model first
            self.legal_model = SentenceTransformer('nlpaueb/legal-bert-base-uncased')
            logger.info("Loaded nlpaueb/legal-bert-base-uncased model")
        except Exception as e:
            logger.warning(f"Could not load legal-bert model: {e}")
            try:
                # Fallback to general high-performance model
                self.legal_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')
                logger.info("Loaded all-mpnet-base-v2 fallback model")
            except Exception as e2:
                logger.warning(f"Could not load fallback model: {e2}")
                # Final fallback to lightweight model
                self.legal_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                logger.info("Loaded all-MiniLM-L6-v2 minimal model")

    def _create_bm25_index(self) -> None:
        """Create BM25 index for keyword search"""
        tokenized_docs = []

        for doc in self.documents:
            # Tokenize and clean
            tokens = self._tokenize_legal_text(doc)
            tokenized_docs.append(tokens)

        self.bm25_index = BM25Okapi(tokenized_docs)
        logger.info("BM25 index created successfully")

    def _tokenize_legal_text(self, text: str) -> List[str]:
        """Tokenize legal text with specific preprocessing"""
        # Convert to lowercase
        text = text.lower()

        # Replace common legal abbreviations
        text = re.sub(r'\bs\.\s*(\d+)', r'section \1', text)  # s. 5 -> section 5
        text = re.sub(r'\bss\.\s*(\d+)', r'sections \1', text)  # ss. 5 -> sections 5

        # Tokenize
        tokens = word_tokenize(text)

        # Filter tokens
        filtered_tokens = []
        for token in tokens:
            # Keep alphanumeric tokens, section numbers, and legal references
            if (token.isalnum() and
                len(token) > 2 and
                token not in self.stop_words):
                filtered_tokens.append(token)
            elif re.match(r'\d+[a-z]*', token):  # Keep section numbers like "9a", "27"
                filtered_tokens.append(token)

        return filtered_tokens

    def _create_embeddings(self) -> None:
        """Create semantic embeddings using Legal-BERT"""
        if not self.legal_model:
            raise ValueError("Legal model not loaded")

        # Generate embeddings in batches
        batch_size = 16
        embeddings_list = []

        for i in range(0, len(self.documents), batch_size):
            batch = self.documents[i:i + batch_size]
            batch_embeddings = self.legal_model.encode(
                batch,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            embeddings_list.append(batch_embeddings)

            logger.info(f"Generated embeddings for batch {i//batch_size + 1}/{(len(self.documents) + batch_size - 1)//batch_size}")

        self.embeddings = np.vstack(embeddings_list)
        logger.info(f"Generated embeddings shape: {self.embeddings.shape}")

    def _save_to_cache(self) -> None:
        """Save index components to cache"""
        logger.info("Saving to cache...")

        # Save documents
        with open(self.documents_cache, 'wb') as f:
            pickle.dump(self.documents, f)

        # Save BM25 index
        with open(self.bm25_cache, 'wb') as f:
            pickle.dump(self.bm25_index, f)

        # Save embeddings
        np.save(self.embeddings_cache, self.embeddings)

        # Save metadata
        with open(self.metadata_cache, 'w') as f:
            json.dump(self.document_metadata, f, indent=2)

        logger.info("Cache saved successfully")

    def _load_from_cache(self) -> None:
        """Load index components from cache"""
        # Load documents
        with open(self.documents_cache, 'rb') as f:
            self.documents = pickle.load(f)

        # Load BM25 index
        with open(self.bm25_cache, 'rb') as f:
            self.bm25_index = pickle.load(f)

        # Load embeddings
        self.embeddings = np.load(self.embeddings_cache)

        # Load metadata
        with open(self.metadata_cache, 'r') as f:
            self.document_metadata = json.load(f)

        # Load model for query encoding
        self._load_legal_model()

        logger.info("Loaded from cache successfully")

    def search(self, query: str, top_k: int = 5, revenue_type_filter: Optional[str] = None) -> List[Dict]:
        """
        Perform hybrid search combining BM25 and semantic search

        Args:
            query: Search query
            top_k: Number of results to return
            revenue_type_filter: Optional filter by revenue type

        Returns:
            List of search results with scores and metadata
        """
        if not self.bm25_index or self.embeddings is None:
            raise ValueError("Search engine not initialized. Call initialize() first.")

        # Apply revenue type filter
        if revenue_type_filter:
            filtered_indices = [i for i, meta in enumerate(self.document_metadata)
                              if meta['revenue_type'] == revenue_type_filter]
            if not filtered_indices:
                logger.warning(f"No documents found for revenue type: {revenue_type_filter}")
                return []
        else:
            filtered_indices = list(range(len(self.documents)))

        # Perform BM25 search
        bm25_results = self._bm25_search(query, filtered_indices, top_k=min(20, len(filtered_indices)))

        # Perform semantic search
        semantic_results = self._semantic_search(query, filtered_indices, top_k=min(20, len(filtered_indices)))

        # Combine results using Reciprocal Rank Fusion
        combined_results = self._reciprocal_rank_fusion(bm25_results, semantic_results, top_k)

        return combined_results

    def _bm25_search(self, query: str, filtered_indices: List[int], top_k: int) -> List[Tuple[int, float]]:
        """Perform BM25 keyword search"""
        query_tokens = self._tokenize_legal_text(query)

        if not query_tokens:
            return []

        # Get scores for all documents
        all_scores = self.bm25_index.get_scores(query_tokens)

        # Filter and sort results
        filtered_results = [(i, all_scores[i]) for i in filtered_indices if all_scores[i] > 0]
        filtered_results.sort(key=lambda x: x[1], reverse=True)

        return filtered_results[:top_k]

    def _semantic_search(self, query: str, filtered_indices: List[int], top_k: int) -> List[Tuple[int, float]]:
        """Perform semantic search using Legal-BERT"""
        # Generate query embedding
        query_embedding = self.legal_model.encode([query], convert_to_numpy=True)

        # Filter embeddings
        filtered_embeddings = self.embeddings[filtered_indices]

        # Calculate similarities
        similarities = cosine_similarity(query_embedding, filtered_embeddings)[0]

        # Create results with original indices
        results = [(filtered_indices[i], similarities[i]) for i in range(len(similarities))]
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def _reciprocal_rank_fusion(self, bm25_results: List[Tuple[int, float]],
                               semantic_results: List[Tuple[int, float]],
                               top_k: int) -> List[Dict]:
        """Combine BM25 and semantic search results using RRF"""
        def rrf_score(rank: int, k: int = 60) -> float:
            return 1 / (k + rank + 1)

        # Create score dictionary
        combined_scores = {}

        # Add semantic search scores (70% weight)
        for rank, (doc_idx, score) in enumerate(semantic_results):
            combined_scores[doc_idx] = combined_scores.get(doc_idx, 0) + 0.7 * rrf_score(rank)

        # Add BM25 scores (30% weight)
        for rank, (doc_idx, score) in enumerate(bm25_results):
            combined_scores[doc_idx] = combined_scores.get(doc_idx, 0) + 0.3 * rrf_score(rank)

        # Sort by combined score
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

        # Format results
        final_results = []
        for doc_idx, combined_score in sorted_results[:top_k]:
            # Get original scores
            bm25_score = next((score for idx, score in bm25_results if idx == doc_idx), 0.0)
            semantic_score = next((score for idx, score in semantic_results if idx == doc_idx), 0.0)

            result = {
                'content': self.documents[doc_idx],
                'metadata': self.document_metadata[doc_idx],
                'combined_score': combined_score,
                'bm25_score': bm25_score,
                'semantic_score': semantic_score,
                'document_index': doc_idx
            }
            final_results.append(result)

        return final_results

    def list_revenue_types(self) -> List[str]:
        """List all available revenue types"""
        revenue_types = set(meta['revenue_type'] for meta in self.document_metadata)
        return sorted(list(revenue_types))

    def get_statistics(self) -> Dict:
        """Get search engine statistics"""
        if not self.document_metadata:
            return {}

        revenue_type_counts = {}
        for meta in self.document_metadata:
            rt = meta['revenue_type']
            revenue_type_counts[rt] = revenue_type_counts.get(rt, 0) + 1

        return {
            'total_documents': len(self.documents),
            'total_files': len(set(meta['file_path'] for meta in self.document_metadata)),
            'revenue_types': revenue_type_counts,
            'embedding_dimension': self.embeddings.shape[1] if self.embeddings is not None else 0,
            'cache_exists': self._cache_exists()
        }

def main():
    """Test the hybrid search engine"""
    engine = HybridSearchEngine()

    # Initialize
    print("🔄 Initializing hybrid search engine...")
    engine.initialize()

    # Show statistics
    stats = engine.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"  Total documents: {stats['total_documents']}")
    print(f"  Total files: {stats['total_files']}")
    print(f"  Revenue types: {len(stats['revenue_types'])}")
    print(f"  Embedding dimension: {stats['embedding_dimension']}")

    # Test queries
    test_queries = [
        "What is the current land tax rate in NSW?",
        "How do I calculate payroll tax?",
        "What are the motor vehicle registration fees?",
        "Gaming machine tax rates for clubs",
        "Coal royalty payment requirements"
    ]

    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")
        results = engine.search(query, top_k=3)

        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['metadata']['act_name']} - {result['metadata']['section_title']}")
            print(f"     Combined: {result['combined_score']:.3f} | BM25: {result['bm25_score']:.3f} | Semantic: {result['semantic_score']:.3f}")
            print(f"     Type: {result['metadata']['revenue_type']}")

if __name__ == "__main__":
    main()